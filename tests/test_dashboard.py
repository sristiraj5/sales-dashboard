"""Run with: python -m pytest -q"""

from datetime import date

import pytest

from src.analytics import (
    SalesFilters, count_orders, get_breakdown, get_kpis, get_monthly_trend,
    get_orders, get_top_products,
)
from src.db import add_order, connect, get_products, initialize_database
from src.sample_data import generate_demo_csv


@pytest.fixture
def test_db(tmp_path):
    path = tmp_path / "orders.db"
    initialize_database(path, load_demo=False)
    with connect(path) as conn:
        # Known values make revenue/return-rate assertions easy to verify.
        conn.executemany(
            """INSERT INTO orders
                (order_id,order_date,customer_id,sku,quantity,unit_price,unit_cost,
                 discount,region,channel,payment_method,status)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            [
                ("T-001", "2026-01-04", "C001", "EL-101", 2, 3000, 1800, .10, "North", "Website", "UPI", "Delivered"),
                ("T-002", "2026-01-05", "C002", "EL-101", 1, 3000, 1800, .00, "South", "Mobile App", "UPI", "Returned"),
                ("T-003", "2026-02-02", "C003", "FA-201", 1, 800, 300, .00, "North", "Website", "UPI", "Cancelled"),
                ("T-004", "2026-02-03", "C001", "FA-201", 3, 800, 300, .25, "North", "Retail Store", "UPI", "Delivered"),
            ],
        )
    return path


@pytest.fixture
def filters():
    return SalesFilters(date(2026, 1, 1), date(2026, 2, 28))


def test_kpis_do_not_count_returns_as_sales(test_db, filters):
    k = get_kpis(filters, test_db)
    assert k["all_orders"] == 4
    assert k["delivered_orders"] == 2
    assert k["returned_orders"] == 1
    assert k["total_revenue"] == pytest.approx(7200)  # 2*3000*.9 + 3*800*.75
    assert k["gross_profit"] == pytest.approx(2700)   # (5400-3600) + (1800-900)
    assert k["aov"] == pytest.approx(3600)
    assert k["margin_pct"] == pytest.approx(37.5)
    assert k["return_pct"] == pytest.approx(25)
    assert k["active_customers"] == 1


def test_filters_affect_aggregates(test_db, filters):
    filtered = SalesFilters(filters.start_date, filters.end_date, ("South",))
    k = get_kpis(filtered, test_db)
    assert k["all_orders"] == 1
    assert k["total_revenue"] == 0
    electronics = SalesFilters(filters.start_date, filters.end_date, categories=("Electronics",))
    assert get_kpis(electronics, test_db)["total_revenue"] == 5400
    channels = SalesFilters(filters.start_date, filters.end_date, channels=("Website",))
    assert get_kpis(channels, test_db)["all_orders"] == 2


def test_monthly_trend_and_products(test_db, filters):
    trend = get_monthly_trend(filters, test_db)
    assert list(trend["month"]) == ["2026-01", "2026-02"]
    assert list(trend["revenue"]) == [5400, 1800]
    products = get_top_products(filters, test_db)
    assert products.iloc[0]["product_name"] == "Wireless Headphones"
    assert products["revenue"].sum() == 7200
    regions = get_breakdown(filters, "region", test_db)
    assert regions["revenue"].sum() == 7200


def test_parameterized_search_and_pagination(test_db, filters):
    assert count_orders(filters, "C001", test_db) == 2
    assert count_orders(filters, "' OR 1=1 --", test_db) == 0
    assert len(get_orders(filters, limit=2, offset=2, db_path=test_db)) == 2
    assert len(get_orders(filters, search="%", db_path=test_db)) == 0
    with pytest.raises(ValueError):
        get_breakdown(filters, "region; DROP TABLE orders;", test_db)


def test_add_order_and_validation(test_db, filters):
    id_value = add_order(
        order_date=date(2026, 2, 20), customer_id="USER-001", sku="SP-401",
        quantity=2, discount_pct=10, region="West", channel="Website",
        payment_method="UPI", status="Delivered", db_path=test_db,
    )
    assert id_value.startswith("NEW-")
    assert get_kpis(filters, test_db)["all_orders"] == 5
    assert count_orders(filters, id_value, test_db) == 1
    with pytest.raises(ValueError):
        add_order(order_date=date.today(), customer_id="", sku="SP-401", quantity=2,
                  discount_pct=0, region="West", channel="Website",
                  payment_method="UPI", status="Delivered", db_path=test_db)
    with pytest.raises(ValueError):
        add_order(order_date=date.today(), customer_id="C1", sku="NOT-A-SKU", quantity=2,
                  discount_pct=0, region="West", channel="Website",
                  payment_method="UPI", status="Delivered", db_path=test_db)
    assert len(get_products(test_db)) == 24


def test_empty_date_window(test_db):
    blank = SalesFilters(date(2024, 1, 1), date(2024, 12, 31))
    assert get_kpis(blank, test_db)["total_revenue"] == 0
    assert get_monthly_trend(blank, test_db).empty
    assert get_orders(blank, db_path=test_db).empty


def test_demo_generator_deterministic(tmp_path):
    file_a = generate_demo_csv(tmp_path / "a.csv", rows=12, seed=123)
    file_b = generate_demo_csv(tmp_path / "b.csv", rows=12, seed=123)
    assert file_a.read_bytes() == file_b.read_bytes()
    assert len(file_a.read_text().splitlines()) == 13
