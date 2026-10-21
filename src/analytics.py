"""Reusable, parameterized SQL queries powering the dashboard.

All reports query SQLite, rather than aggregating the demo CSV in Python.
"""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

from src.db import DEFAULT_DB, read_sql


@dataclass(frozen=True)
class SalesFilters:
    start_date: date
    end_date: date
    regions: tuple[str, ...] = field(default_factory=tuple)
    categories: tuple[str, ...] = field(default_factory=tuple)
    channels: tuple[str, ...] = field(default_factory=tuple)


def _where(filters: SalesFilters) -> tuple[str, tuple]:
    """Build WHERE text from trusted column names and bound values."""
    conditions = ["o.order_date BETWEEN ? AND ?"]
    params: list = [filters.start_date.isoformat(), filters.end_date.isoformat()]
    for column, values in (
        ("o.region", filters.regions),
        ("p.category", filters.categories),
        ("o.channel", filters.channels),
    ):
        if values:
            conditions.append(f"{column} IN ({','.join('?' for _ in values)})")
            params.extend(values)
    return " AND ".join(conditions), tuple(params)


def _base(filters: SalesFilters) -> tuple[str, tuple]:
    condition, params = _where(filters)
    query = f"""
        WITH filtered AS (
            SELECT o.order_id, o.order_date, o.customer_id,
                   o.sku, p.product_name, p.category, o.quantity,
                   o.unit_price, o.unit_cost, o.discount, o.region,
                   o.channel, o.payment_method, o.status,
                   CASE WHEN o.status = 'Delivered'
                        THEN o.quantity * o.unit_price * (1 - o.discount)
                        ELSE 0 END AS revenue,
                   CASE WHEN o.status = 'Delivered'
                        THEN o.quantity * (o.unit_price * (1 - o.discount) - o.unit_cost)
                        ELSE 0 END AS profit
            FROM orders o JOIN products p ON o.sku = p.sku
            WHERE {condition}
        )
    """
    return query, params


def get_kpis(filters: SalesFilters, db_path: Path = DEFAULT_DB) -> dict:
    base, params = _base(filters)
    query = base + """
        SELECT COUNT(*) AS all_orders,
               COALESCE(SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END), 0) AS delivered_orders,
               COALESCE(SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END), 0) AS returned_orders,
               COALESCE(SUM(revenue), 0) AS total_revenue,
               COALESCE(SUM(profit), 0) AS gross_profit,
               COALESCE(SUM(CASE WHEN status = 'Delivered' THEN quantity ELSE 0 END), 0) AS units_sold,
               COUNT(DISTINCT CASE WHEN status = 'Delivered' THEN customer_id END) AS active_customers
        FROM filtered
    """
    row = read_sql(query, params, db_path).iloc[0].to_dict()
    delivered = row["delivered_orders"]
    all_orders = row["all_orders"]
    sales = row["total_revenue"]
    row["aov"] = sales / delivered if delivered else 0
    row["margin_pct"] = 100 * row["gross_profit"] / sales if sales else 0
    row["return_pct"] = 100 * row["returned_orders"] / all_orders if all_orders else 0
    return row


def get_monthly_trend(filters: SalesFilters, db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    base, params = _base(filters)
    return read_sql(base + """
        SELECT substr(order_date, 1, 7) AS month,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit,
               SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS orders
        FROM filtered GROUP BY substr(order_date, 1, 7) ORDER BY month
    """, params, db_path)


def get_breakdown(filters: SalesFilters, dimension: str, db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    """Whitelisted dimensions prevent dynamic SQL injection."""
    if dimension not in ("region", "category", "channel", "status"):
        raise ValueError("Invalid breakdown dimension")
    base, params = _base(filters)
    return read_sql(base + f"""
        SELECT {dimension} AS segment,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit,
               COUNT(*) AS orders
        FROM filtered GROUP BY {dimension} ORDER BY revenue DESC, segment
    """, params, db_path)


def get_top_products(filters: SalesFilters, db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    base, params = _base(filters)
    return read_sql(base + """
        SELECT sku, product_name, category,
               ROUND(SUM(revenue), 2) AS revenue,
               ROUND(SUM(profit), 2) AS profit,
               SUM(CASE WHEN status = 'Delivered' THEN quantity ELSE 0 END) AS units,
               SUM(CASE WHEN status = 'Delivered' THEN 1 ELSE 0 END) AS orders,
               ROUND(CASE WHEN SUM(revenue) > 0
                    THEN 100.0 * SUM(profit) / SUM(revenue) ELSE 0 END, 1) AS margin_pct
        FROM filtered GROUP BY sku, product_name, category
        ORDER BY revenue DESC, sku
    """, params, db_path)


def get_orders(
    filters: SalesFilters, search: str = "", limit: int | None = 25,
    offset: int = 0, db_path: Path = DEFAULT_DB,
) -> pd.DataFrame:
    base, params = _base(filters)
    suffix = ""
    if search.strip():
        # Escape LIKE wildcards so searches match literal user input.
        term = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        suffix = " WHERE (order_id LIKE ? ESCAPE '\\' OR customer_id LIKE ? ESCAPE '\\' OR product_name LIKE ? ESCAPE '\\')"
        params += (f"%{term}%",) * 3
    query = base + """
        SELECT order_id, order_date, customer_id, product_name, category,
               quantity, unit_price, discount, revenue, profit, region,
               channel, payment_method, status FROM filtered
    """ + suffix + " ORDER BY order_date DESC, order_id DESC"
    if limit is not None:
        if limit < 1 or offset < 0:
            raise ValueError("Pagination must use a positive limit and nonnegative offset")
        query += " LIMIT ? OFFSET ?"
        params += (limit, offset)
    return read_sql(query, params, db_path)


def count_orders(filters: SalesFilters, search: str = "", db_path: Path = DEFAULT_DB) -> int:
    base, params = _base(filters)
    clause = ""
    if search.strip():
        term = search.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clause = " WHERE (order_id LIKE ? ESCAPE '\\' OR customer_id LIKE ? ESCAPE '\\' OR product_name LIKE ? ESCAPE '\\')"
        params += (f"%{term}%",) * 3
    return int(read_sql(base + "SELECT COUNT(*) AS total FROM filtered" + clause, params, db_path).iloc[0, 0])
