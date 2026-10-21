# ↗ SalesPulse — Retail Sales Analytics Dashboard

**A medium-level, resume-ready Python + SQL web application designed to be understood in 14 days.**

SalesPulse analyzes **4,800 completely synthetic retail transactions** across 24 products, 4 categories, 5 regions and 4 purchase channels (January 2025–September 2026). The app runs real SQL queries against a local SQLite database, displays an interactive web dashboard and lets you save new transactions.

> **Portfolio disclosure:** This repository contains fictional demo data, not actual customer, store or company data. Revenue and profit amounts are for demonstration only.

## 1. Features

| Page | What you can do | Skills demonstrated |
| --- | --- | --- |
| **Overview** | KPI cards, monthly revenue/profit trend, category donut, region/channel revenue, top products and return breakdown | SQL aggregations, KPI design, Plotly |
| **Product Insights** | Top 10 products, category profitability, revenue-vs-margin bubble chart, product scorecard and CSV export | SQL JOIN, product analytics, pandas |
| **Order Explorer** | Filter by date, region, category and channel; search transaction IDs, customers and products; paginate and export | SQL WHERE, bound parameters, pagination |
| **Add Order** | Add a validated retail order and store it in SQLite | SQL INSERT, validation, database transactions |

**Business rules:** Revenue is the discounted value of **delivered** orders only: `quantity * unit_price * (1 - discount)`. Gross profit is `revenue - (quantity * unit_cost)`. Returned/cancelled orders contribute **₹0** to net sales and profit but still count toward order-status/return-rate calculations. One transaction row is one order containing one product line. This is a deliberate simplification for the learning project; production carts typically have an `order_items` table.

## 2. Tech stack

- **Python 3.10+** — app code and data handling.
- **SQLite** (built-in `sqlite3`) — relational database, primary/foreign keys, transactions and indexes.
- **SQL** — `JOIN`, `WHERE`, `CASE WHEN`, `GROUP BY`, `COUNT(DISTINCT)`, CTEs, pagination and prepared parameters.
- **Streamlit** — interactive Python web UI, forms, filters and tables.
- **Plotly** — interactive line, bar, donut and bubble charts.
- **pandas** — SQL results and CSV export.
- **pytest** — automated unit/integration tests.

No JavaScript, separate API server, paid services or database account is needed.

## 3. Run locally (Windows, macOS or Linux)

**Prerequisites:** Python 3.10 or later and an internet connection for the first install.

Unzip the project, then open Terminal / VS Code's terminal in the folder containing `app.py`:

```bash
# Windows:
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux:
python3 -m venv .venv
source .venv/bin/activate

# All systems, after activating the virtual environment:
python -m pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints, normally **http://localhost:8501**. On first start the app creates `data/sales.db` and imports the included synthetic CSV; later launches preserve locally added orders.

**Helpful commands:**

```bash
python -m pytest -q           # run automated tests
python -m src.sample_data     # rebuild the same demo CSV (seed = 42)
```

To reset the *local* app database to fresh demo data, stop Streamlit and delete only `data/sales.db`, then launch again. The CSV remains unchanged.

## 4. Project structure

```text
salespulse_dashboard/
├── app.py                      # UI pages, widgets and Plotly charts
├── src/
│   ├── analytics.py            # parameterized SQL analytics queries
│   ├── db.py                   # schema, database bootstrapping and INSERT
│   ├── catalog.py              # fictional product catalog and constants
│   └── sample_data.py          # deterministic synthetic CSV generator
├── seed/
│   └── demo_orders.csv         # 4,800 fake example orders
├── sql/
│   └── learning_queries.sql    # readable SQL practice examples
├── tests/
│   └── test_dashboard.py       # correctness tests
├── .streamlit/
│   └── config.toml             # custom theme
├── requirements.txt
├── LEARNING_PLAN.md            # 14-day, 2-hours-a-day study roadmap
└── README.md
```

### Architecture

```text
Browser → Streamlit pages (app.py)
                 ↓
      Python analytics functions
                 ↓
       Parameterized SQL queries
                 ↓
      SQLite (data/sales.db)
                 ↑
        Seed CSV / Add Order form
```

There are two tables. `products` stores SKU, name, category, retail price and unit cost. `orders` stores date, customer ID, SKU (foreign key), quantity, selling-price and cost snapshots, discount, region, channel, payment method and order status. Keeping the historical price snapshot means changing a future catalog price would not change an old order's reported revenue.
