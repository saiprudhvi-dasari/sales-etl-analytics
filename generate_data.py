"""Generate synthetic sales transactions (with realistic messiness).

Intentionally includes the kind of dirt you find in real extracts:
duplicate rows, a few nulls, some negative quantities (returns entered
wrong), and inconsistent date formats. The ETL pipeline cleans all of it.
"""
import numpy as np
import pandas as pd

RNG = np.random.default_rng(7)
N = 8000

PRODUCTS = {
    "P-101": ("Wireless Mouse", "Accessories", 29.99),
    "P-102": ("Mechanical Keyboard", "Accessories", 89.99),
    "P-103": ("USB-C Hub", "Accessories", 49.99),
    "P-104": ("Laptop Stand", "Accessories", 59.99),
    "P-201": ("Ultrabook 14", "Computers", 1199.00),
    "P-202": ("Workstation 16", "Computers", 1899.00),
    "P-203": ("Tablet 11", "Computers", 549.00),
    "P-301": ("Noise-Cancelling Headphones", "Audio", 249.99),
    "P-302": ("Bluetooth Speaker", "Audio", 129.99),
    "P-303": ("Earbuds Pro", "Audio", 179.99),
}
REGIONS = ["North", "South", "East", "West"]
SEGMENTS = ["Consumer", "Corporate", "Education"]


def main():
    ids = list(PRODUCTS.keys())
    # Popular products sell more: weight the draw.
    weights = np.array([3, 2, 2, 1, 1.5, 0.8, 1.2, 1.5, 1, 1.2])
    weights /= weights.sum()

    picks = RNG.choice(ids, N, p=weights)
    names = [PRODUCTS[p][0] for p in picks]
    cats = [PRODUCTS[p][1] for p in picks]
    prices = np.array([PRODUCTS[p][2] for p in picks])

    dates = pd.to_datetime("2024-01-01") + pd.to_timedelta(
        RNG.integers(0, 365, N), unit="D"
    )
    # A few rows with a different date format, like a merged second source.
    datestr = dates.strftime("%Y-%m-%d").to_numpy()
    mask = RNG.random(N) < 0.05
    datestr[mask] = dates[mask].strftime("%m/%d/%Y").to_numpy()

    df = pd.DataFrame({
        "order_id": [f"ORD-{100000 + i}" for i in range(N)],
        "order_date": datestr,
        "region": RNG.choice(REGIONS, N, p=[0.3, 0.2, 0.25, 0.25]),
        "product_id": picks,
        "product_name": names,
        "category": cats,
        "customer_segment": RNG.choice(SEGMENTS, N, p=[0.55, 0.3, 0.15]),
        "quantity": RNG.integers(1, 6, N),
        "unit_price": np.round(prices, 2),
    })

    # --- dirt ---
    df = pd.concat([df, df.sample(120, random_state=1)], ignore_index=True)  # dupes
    df.loc[RNG.choice(df.index, 60), "region"] = None                        # nulls
    df.loc[RNG.choice(df.index, 40), "quantity"] = -1                        # bad returns
    df.loc[RNG.choice(df.index, 25), "unit_price"] = 0                       # zero prices

    out = "data/sales_raw.csv"
    df.to_csv(out, index=False)
    print(f"Wrote {out}: {len(df):,} rows (includes intentional duplicates/dirt)")


if __name__ == "__main__":
    main()
