# Learn SalesPulse in 14 days

**Goal:** Understand the code well enough to customize it, deploy it and explain the SQL queries during an internship or junior analyst interview. Budget around **1.5–2.5 hours/day**. You are expected to edit the project yourself, not memorize everything.

| Day | Focus | What to do | Deliverable |
|---|---|---|---|
| **1** | Environment | Install Python and VS Code, create `.venv`, run `streamlit run app.py`, navigate all four pages. | App launches locally. |
| **2** | Python basics | Study functions, loops, dictionaries and imports in `catalog.py` and `sample_data.py`. | Explain how demo data is generated. |
| **3** | pandas | Inspect `demo_orders.csv` with pandas, group by region and compute a total. | A small notebook or script with 3 results. |
| **4** | SQL fundamentals | Learn `SELECT`, `WHERE`, `ORDER BY`, `LIMIT`. Open database with SQLite Browser. | Retrieve 10 recent delivered orders. |
| **5** | SQL analytics | Practice `SUM`, `COUNT`, `GROUP BY`, `CASE WHEN` and net revenue. | Write a query for revenue by region. |
| **6** | Joins & data model | Understand primary keys, product SKU and `JOIN`, plus price snapshots. | Draw the 2-table entity relationship diagram. |
| **7** | SQL CTE & filters | Read `_base()` and `_where()` in `analytics.py`. Try 2 filters. | Explain how placeholders prevent SQL injection. |
| **8** | Streamlit | Explore `st.columns`, `st.sidebar`, `st.multiselect` and `st.date_input`. | Change one page header and add a new filter description. |
| **9** | KPI formulas | Follow `get_kpis()` from SQL to the six KPI cards. | Recalculate sample revenue/profit with SQL. |
| **10** | Visualization | Read 3 Plotly charts in `app.py`; change a color or chart type. | One customized chart. |
| **11** | Orders & exports | Trace search → query → pagination → CSV. | Explain why export isn't limited to one page. |
| **12** | Forms & tests | Add an order, inspect the inserted row; run `pytest`. | Tests pass; record a new order ID. |
| **13** | Deployment | Push code to GitHub, deploy to Streamlit Community Cloud, test filters. | GitHub repo + public demo link. |
| **14** | Portfolio polish | Add screenshots, write resume bullets, practice the interview questions. | Present the dashboard in a 3-minute walkthrough. |

## Skills checkpoint (do without notes)

1. Write a SQL query to calculate revenue for `Delivered` orders by region.
2. Explain the difference between `unit_price`, `unit_cost`, `discount`, `revenue` and `profit`.
3. Explain how a Streamlit sidebar selection changes SQL query results.
4. Explain why the app uses bound parameters (`?`) instead of putting user-entered text inside SQL.
5. Demonstrate searching for an order, exporting a filtered CSV and adding a new order.
6. Show the tests and explain one simple improvement you would make next.

## Sensible extensions (after day 14)

- Add **month-over-month growth** to KPI cards.
- Add a **customer segmentation** page with repeat purchases and RFM scores.
- Introduce an `order_items` table to support shopping carts with many products.
- Add Docker, GitHub Actions tests or migrate from SQLite to PostgreSQL.

Do not claim any of these extensions on your resume until you actually implement them.
