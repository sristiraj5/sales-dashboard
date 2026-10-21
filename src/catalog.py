"""Small fictional retail product catalog used by the demo."""

PRODUCTS = [
    ("EL-101", "Wireless Headphones", "Electronics", 2999.0, 1810.0),
    ("EL-102", "Bluetooth Speaker", "Electronics", 2199.0, 1380.0),
    ("EL-103", "Smartwatch", "Electronics", 4499.0, 3120.0),
    ("EL-104", "Power Bank", "Electronics", 1399.0, 820.0),
    ("EL-105", "Mechanical Keyboard", "Electronics", 3499.0, 2380.0),
    ("EL-106", "Webcam HD", "Electronics", 2599.0, 1590.0),
    ("FA-201", "Cotton T-Shirt", "Fashion", 799.0, 330.0),
    ("FA-202", "Denim Jacket", "Fashion", 2799.0, 1600.0),
    ("FA-203", "Running Shoes", "Fashion", 3299.0, 1940.0),
    ("FA-204", "Casual Backpack", "Fashion", 1899.0, 990.0),
    ("FA-205", "Summer Dress", "Fashion", 2299.0, 1190.0),
    ("FA-206", "Sunglasses", "Fashion", 1099.0, 495.0),
    ("HM-301", "Ceramic Mug Set", "Home & Living", 999.0, 445.0),
    ("HM-302", "Desk Lamp", "Home & Living", 1799.0, 895.0),
    ("HM-303", "Bedsheet Set", "Home & Living", 2099.0, 1070.0),
    ("HM-304", "Air Purifier", "Home & Living", 6999.0, 4750.0),
    ("HM-305", "Water Bottle", "Home & Living", 649.0, 260.0),
    ("HM-306", "Storage Baskets", "Home & Living", 1199.0, 605.0),
    ("SP-401", "Yoga Mat", "Sports & Fitness", 1099.0, 510.0),
    ("SP-402", "Resistance Bands", "Sports & Fitness", 799.0, 300.0),
    ("SP-403", "Dumbbell Set", "Sports & Fitness", 2899.0, 1680.0),
    ("SP-404", "Fitness Tracker", "Sports & Fitness", 3699.0, 2420.0),
    ("SP-405", "Skipping Rope", "Sports & Fitness", 499.0, 185.0),
    ("SP-406", "Gym Duffel Bag", "Sports & Fitness", 1599.0, 820.0),
]

REGIONS = ("North", "South", "East", "West", "Central")
CHANNELS = ("Website", "Mobile App", "Marketplace", "Retail Store")
STATUSES = ("Delivered", "Returned", "Cancelled")
PAYMENT_METHODS = ("UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Net Banking")

CSV_COLUMNS = (
    "order_id", "order_date", "customer_id", "sku", "quantity",
    "unit_price", "unit_cost", "discount", "region", "channel", "payment_method", "status",
)
