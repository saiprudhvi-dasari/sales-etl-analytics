# Sales ETL + Analytics

A small end-to-end pipeline: generate messy sales data, clean it, load it
into SQLite, and produce dashboard-ready aggregates plus charts.

## What it is

`generate_data.py` creates 8,000 synthetic transactions across 10 products,
4 regions, and 3 customer segments — deliberately messy the way real extracts
are: duplicate rows, null regions, negative quantities, mixed date formats.
`etl.py` cleans all of it and loads four tables into SQLite. `charts.py`
plots monthly revenue, top products, and regional share as PNGs.

## Why I built it

Every analytics role I've had involved some version of "here's a CSV, make
it trustworthy." I wanted a repo that shows that unglamorous work done
properly: explicit data-quality checks with counts printed at each step, not
a silent `dropna()` and hope. The aggregates (`monthly_revenue`,
`top_products`, `regional_monthly`) are shaped the way I'd hand them to a
BI tool.

## How to run

```bash
pip install -r requirements.txt
python generate_data.py   # creates data/sales_raw.csv
python etl.py             # cleans + loads data/sales.db, prints what it removed
python charts.py          # saves PNGs to output/
```

Then poke at the database yourself:

```bash
sqlite3 data/sales.db "SELECT * FROM monthly_revenue ORDER BY month LIMIT 5;"
```

## What's inside

- `generate_data.py` — synthetic transactions with seeded randomness and
  intentional dirt (see the `# --- dirt ---` section for exactly what's dirty).
- `etl.py` — extract → transform → load. Dedupes, coerces two date formats,
  drops bad quantities/prices, fills null regions with "Unknown", adds
  `line_total` and `order_month`, then writes `sales_clean` plus three
  aggregate tables.
- `charts.py` — three matplotlib charts saved to `output/`.

## What I'd improve

- **The DB rebuild is blunt.** `etl.py` deletes and recreates the SQLite file
  every run. Fine for 8k rows; a real pipeline would do incremental loads
  with a watermark on `order_date`.
- **No tests on the transforms.** The print statements show row counts, but
  there are no assertions (e.g., "no negative quantities in output"). Adding
  a few would take 20 minutes and I'd do it next.
- **Validation is rule-based, not statistical.** It catches format errors but
  wouldn't catch a real anomaly like "revenue dropped 40% this month because
  a source feed broke." A proper pipeline would add anomaly checks on the
  aggregates.
- **Charts are static PNGs.** Good enough for a portfolio, but in practice
  these tables would feed Power BI or Tableau, not matplotlib.
