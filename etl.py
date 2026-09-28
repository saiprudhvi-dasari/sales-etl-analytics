"""ETL: clean the raw sales extract and load analytics tables into SQLite.

Extract  -> data/sales_raw.csv
Transform -> dedupe, fix dates/quantities/prices, add line totals + month
Load     -> data/sales.db with raw + aggregated tables:
            sales_clean, monthly_revenue, top_products, regional_monthly

Usage: python etl.py
"""
import sqlite3
from pathlib import Path

import pandas as pd

RAW = Path("data/sales_raw.csv")
DB = Path("data/sales.db")


def extract() -> pd.DataFrame:
    df = pd.read_csv(RAW)
    print(f"Extracted {len(df):,} rows")
    return df


def transform(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    before = len(df)

    # Drop exact duplicates, keeping the first occurrence.
    df = df.drop_duplicates()
    dupes = before - len(df)

    # Dates arrive in two formats (a merged second source); parse per-element.
    df["order_date"] = pd.to_datetime(df["order_date"], format="mixed",
                                      errors="coerce")
    bad_dates = df["order_date"].isna().sum()
    df = df.dropna(subset=["order_date"])

    # Negative quantities and zero prices are entry errors, not real orders.
    bad_qty = (df["quantity"] <= 0).sum()
    bad_price = (df["unit_price"] <= 0).sum()
    df = df[(df["quantity"] > 0) & (df["unit_price"] > 0)]

    # Missing region -> "Unknown" rather than dropping the sale.
    null_region = df["region"].isna().sum()
    df["region"] = df["region"].fillna("Unknown")

    df["line_total"] = (df["quantity"] * df["unit_price"]).round(2)
    df["order_month"] = df["order_date"].dt.to_period("M").astype(str)

    print(f"Removed: {dupes} dupes, {bad_dates} bad dates, "
          f"{bad_qty} bad quantities, {bad_price} zero prices; "
          f"filled {null_region} null regions")
    print(f"Clean: {len(df):,} rows")
    return df


def load(df: pd.DataFrame):
    if DB.exists():
        DB.unlink()  # rebuild from scratch each run; fine at this scale
    conn = sqlite3.connect(DB)
    df.to_sql("sales_clean", conn, index=False)

    monthly = df.groupby("order_month", as_index=False)["line_total"].sum()
    monthly.columns = ["month", "revenue"]
    monthly.to_sql("monthly_revenue", conn, index=False)

    top = (df.groupby(["product_id", "product_name", "category"], as_index=False)
             .agg(units=("quantity", "sum"), revenue=("line_total", "sum"))
             .sort_values("revenue", ascending=False).head(10))
    top.to_sql("top_products", conn, index=False)

    regional = (df.groupby(["region", "order_month"], as_index=False)
                  .agg(orders=("order_id", "nunique"), revenue=("line_total", "sum")))
    regional.to_sql("regional_monthly", conn, index=False)

    conn.commit()
    tables = pd.read_sql(
        "SELECT name FROM sqlite_master WHERE type='table'", conn)
    print(f"Loaded tables into {DB}: {', '.join(tables['name'])}")
    conn.close()


def main():
    load(transform(extract()))


if __name__ == "__main__":
    main()
