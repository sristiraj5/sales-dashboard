"""Deterministic sample transactions. All names, customers and orders are fictional."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from src.catalog import CHANNELS, PAYMENT_METHODS, PRODUCTS, REGIONS, CSV_COLUMNS


def generate_demo_csv(output: Path, rows: int = 4800, seed: int = 42) -> Path:
    """Create rows distributed over Jan 2025–Sep 2026, with light seasonality."""
    output.parent.mkdir(parents=True, exist_ok=True)
    randomizer = random.Random(seed)
    start = date(2025, 1, 1)
    end = date(2026, 9, 30)
    days = [start + timedelta(days=offset) for offset in range((end - start).days + 1)]
    # Late dates, festive months and weekends get slightly more activity.
    weights = [
        (1.0 + 0.30 * (day - start).days / (end - start).days)
        * (1.45 if day.month in (10, 11, 12) else 1.0)
        * (1.12 if day.weekday() >= 5 else 1.0)
        for day in days
    ]
    selected_days = randomizer.choices(days, weights=weights, k=rows)
    selected_days.sort()
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for index, day in enumerate(selected_days, start=1):
            sku, _name, _category, price, cost = randomizer.choice(PRODUCTS)
            # A small subset of high-volume, promo purchases.
            quantity = randomizer.choices([1, 2, 3, 4], weights=[62, 26, 9, 3])[0]
            discount = randomizer.choices([0, 0.05, 0.10, 0.15, 0.20], weights=[50, 17, 16, 12, 5])[0]
            status = randomizer.choices(["Delivered", "Returned", "Cancelled"], weights=[88, 7, 5])[0]
            writer.writerow({
                "order_id": f"ORD-{index:06d}",
                "order_date": day.isoformat(),
                "customer_id": f"CUS-{randomizer.randint(1, 925):04d}",
                "sku": sku,
                "quantity": quantity,
                "unit_price": price,
                "unit_cost": cost,
                "discount": discount,
                "region": randomizer.choices(REGIONS, weights=[26, 25, 14, 25, 10])[0],
                "channel": randomizer.choices(CHANNELS, weights=[36, 35, 20, 9])[0],
                "payment_method": randomizer.choices(PAYMENT_METHODS, weights=[42, 20, 16, 14, 8])[0],
                "status": status,
            })
    return output


if __name__ == "__main__":
    target = Path(__file__).resolve().parents[1] / "seed" / "demo_orders.csv"
    print(f"Generated {generate_demo_csv(target)}")
