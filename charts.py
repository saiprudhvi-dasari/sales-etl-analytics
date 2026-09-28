"""Chart the aggregated tables from the ETL run.

Reads data/sales.db (run etl.py first) and saves PNGs to output/:
monthly revenue trend, top products by revenue, revenue share by region.
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # no display needed; just write files
import matplotlib.pyplot as plt
import pandas as pd

DB = Path("data/sales.db")
OUT = Path("output")
plt.style.use("seaborn-v0_8-whitegrid")


def main():
    OUT.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB)

    # 1. Monthly revenue trend
    monthly = pd.read_sql("SELECT * FROM monthly_revenue ORDER BY month", conn)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(monthly["month"], monthly["revenue"], marker="o")
    ax.set_title("Monthly Revenue — 2024")
    ax.set_ylabel("Revenue ($)")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    fig.savefig(OUT / "monthly_revenue.png", dpi=120)
    plt.close(fig)

    # 2. Top products by revenue
    top = pd.read_sql("SELECT * FROM top_products", conn)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(top["product_name"][::-1], top["revenue"][::-1])
    ax.set_title("Top 10 Products by Revenue")
    ax.set_xlabel("Revenue ($)")
    fig.tight_layout()
    fig.savefig(OUT / "top_products.png", dpi=120)
    plt.close(fig)

    # 3. Revenue share by region
    regional = pd.read_sql(
        "SELECT region, SUM(revenue) AS revenue FROM regional_monthly "
        "GROUP BY region", conn)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(regional["revenue"], labels=regional["region"], autopct="%1.0f%%",
           startangle=90)
    ax.set_title("Revenue Share by Region")
    fig.tight_layout()
    fig.savefig(OUT / "revenue_by_region.png", dpi=120)
    plt.close(fig)

    conn.close()
    print(f"Saved charts to {OUT}/: "
          + ", ".join(p.name for p in sorted(OUT.glob('*.png'))))


if __name__ == "__main__":
    main()
