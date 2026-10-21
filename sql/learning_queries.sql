-- Run after first launch:
--   sqlite3 data/sales.db < sql/learning_queries.sql
-- All financial amounts are in INR. Returned and cancelled orders are excluded
-- from sales and profit, but they still count toward order-status statistics.

-- 1) Join normalized products and orders, then calculate net sales.
SELECT o.order_id, o.order_date, p.product_name, p.category,
       o.quantity * o.unit_price * (1 - o.discount) AS net_sales
FROM orders AS o
JOIN products AS p ON p.sku = o.sku
WHERE o.status = 'Delivered'
ORDER BY o.order_date DESC
LIMIT 10;

-- 2) Monthly trend with GROUP BY and string date grouping.
SELECT substr(order_date, 1, 7) AS month,
       ROUND(SUM(quantity * unit_price * (1 - discount)), 2) AS revenue
FROM orders
WHERE status = 'Delivered'
GROUP BY substr(order_date, 1, 7)
ORDER BY month;

-- 3) Revenue and profitability by product category.
SELECT p.category,
       ROUND(SUM(o.quantity * o.unit_price * (1 - o.discount)), 2) AS revenue,
       ROUND(SUM(o.quantity * (o.unit_price * (1 - o.discount) - o.unit_cost)), 2) AS profit
FROM orders AS o
JOIN products AS p ON p.sku = o.sku
WHERE o.status = 'Delivered'
GROUP BY p.category
ORDER BY revenue DESC;

-- 4) Customer ranking using SQL window functions.
WITH customer_sales AS (
    SELECT customer_id,
           ROUND(SUM(quantity * unit_price * (1 - discount)), 2) AS revenue
    FROM orders WHERE status = 'Delivered'
    GROUP BY customer_id
)
SELECT customer_id, revenue,
       DENSE_RANK() OVER (ORDER BY revenue DESC) AS revenue_rank
FROM customer_sales
ORDER BY revenue_rank
LIMIT 10;

-- 5) Cancellation and return rate by channel.
SELECT channel, COUNT(*) AS total_orders,
       SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) AS returns,
       SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancellations,
       ROUND(100.0 * SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) / COUNT(*), 1) AS return_pct
FROM orders GROUP BY channel ORDER BY return_pct DESC;
