"""SQLite schema, safe writes and data access helpers."""

import csv
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import Iterator
from uuid import uuid4

import pandas as pd

from src.catalog import CHANNELS, CSV_COLUMNS, PAYMENT_METHODS, PRODUCTS, REGIONS, STATUSES
from src.sample_data import generate_demo_csv

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "data" / "sales.db"
DEMO_CSV = ROOT / "seed" / "demo_orders.csv"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    sku TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    list_price REAL NOT NULL CHECK(list_price > 0),
    unit_cost REAL NOT NULL CHECK(unit_cost >= 0)
);
CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    order_date TEXT NOT NULL,
    customer_id TEXT NOT NULL,
    sku TEXT NOT NULL REFERENCES products(sku),
    quantity INTEGER NOT NULL CHECK(quantity > 0),
    unit_price REAL NOT NULL CHECK(unit_price > 0),
    unit_cost REAL NOT NULL CHECK(unit_cost >= 0),
    discount REAL NOT NULL CHECK(discount >= 0 AND discount <= 1),
    region TEXT NOT NULL CHECK(region IN ('North','South','East','West','Central')),
    channel TEXT NOT NULL CHECK(channel IN ('Website','Mobile App','Marketplace','Retail Store')),
    payment_method TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('Delivered','Returned','Cancelled'))
);
CREATE INDEX IF NOT EXISTS idx_orders_date ON orders(order_date);
CREATE INDEX IF NOT EXISTS idx_orders_region ON orders(region);
CREATE INDEX IF NOT EXISTS idx_orders_channel ON orders(channel);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_orders_sku ON orders(sku);
"""


@contextmanager
def connect(db_path: Path = DEFAULT_DB) -> Iterator[sqlite3.Connection]:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=10)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialize_database(db_path: Path = DEFAULT_DB, load_demo: bool = True) -> None:
    """Create schema, seed catalog, and import synthetic transactions once."""
    with connect(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR IGNORE INTO products (sku, product_name, category, list_price, unit_cost) VALUES (?,?,?,?,?)",
            PRODUCTS,
        )
        existing = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if load_demo and existing == 0:
        if not DEMO_CSV.exists():
            generate_demo_csv(DEMO_CSV)
        with DEMO_CSV.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        with connect(db_path) as conn:
            conn.executemany(
                "INSERT OR IGNORE INTO orders (" + ",".join(CSV_COLUMNS) + ") VALUES (" + ",".join("?" * len(CSV_COLUMNS)) + ")",
                [tuple(row[column] for column in CSV_COLUMNS) for row in rows],
            )


def read_sql(query: str, params: tuple = (), db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    with connect(db_path) as conn:
        return pd.read_sql_query(query, conn, params=params)


def get_products(db_path: Path = DEFAULT_DB) -> pd.DataFrame:
    return read_sql("SELECT sku, product_name, category, list_price, unit_cost FROM products ORDER BY product_name", db_path=db_path)


def get_date_bounds(db_path: Path = DEFAULT_DB) -> tuple[date, date]:
    with connect(db_path) as conn:
        earliest, latest = conn.execute("SELECT MIN(order_date), MAX(order_date) FROM orders").fetchone()
    today = date.today()
    return (date.fromisoformat(earliest), date.fromisoformat(latest)) if earliest and latest else (today, today)


def add_order(
    *, order_date: date, customer_id: str, sku: str, quantity: int,
    discount_pct: int, region: str, channel: str, payment_method: str,
    status: str, db_path: Path = DEFAULT_DB,
) -> str:
    """Insert a single order, recording current catalog prices as immutable snapshots."""
    customer_id = customer_id.strip()
    if not customer_id or len(customer_id) > 40:
        raise ValueError("Customer ID must be between 1 and 40 characters.")
    if not isinstance(quantity, int) or quantity < 1 or quantity > 100:
        raise ValueError("Quantity must be between 1 and 100.")
    if not isinstance(discount_pct, int) or not (0 <= discount_pct <= 90):
        raise ValueError("Discount must be between 0 and 90 percent.")
    if region not in REGIONS or channel not in CHANNELS or payment_method not in PAYMENT_METHODS or status not in STATUSES:
        raise ValueError("One or more order fields have an invalid value.")
    if not isinstance(order_date, date):
        raise ValueError("Please enter a valid order date.")
    with connect(db_path) as conn:
        catalog_row = conn.execute("SELECT list_price, unit_cost FROM products WHERE sku = ?", (sku,)).fetchone()
        if catalog_row is None:
            raise ValueError("Unknown SKU.")
        order_id = f"NEW-{uuid4().hex[:12].upper()}"
        conn.execute(
            """INSERT INTO orders
            (order_id, order_date, customer_id, sku, quantity, unit_price,
             unit_cost, discount, region, channel, payment_method, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (order_id, order_date.isoformat(), customer_id, sku, quantity,
             catalog_row[0], catalog_row[1], discount_pct / 100, region,
             channel, payment_method, status),
        )
    return order_id
