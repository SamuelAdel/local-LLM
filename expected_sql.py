"""
Gold-standard SQL answers used by evaluate.py, keyed by question id
(matches questions.py).

Each value is either:
  - a single SQL string, or
  - a list/tuple of acceptable SQL strings (any one matching counts as
    correct) -- used where more than one query is an equally valid answer.

Refusal-expected questions (schema genuinely doesn't have the data) use
the REFUSAL_TOKEN string "CANNOT_GENERATE_SQL", matching REFUSAL_TOKEN in
evaluate.py.

NOTE: this file was regenerated from scratch alongside the expanded
questions.py (91 questions). IDs 1-24 reproduce the same intent as the
original 24-question set; if you had a hand-curated expected_sql.py
before, diff it against this one before overwriting, in case any of your
original gold queries differed intentionally (e.g. a specific column
order or alias convention you were relying on elsewhere).
"""

REFUSAL_TOKEN = "CANNOT_GENERATE_SQL"

EXPECTED_SQL = {

    # --------------------------
    # SIMPLE SELECT
    # --------------------------
    1: "SELECT * FROM Customers;",
    2: "SELECT * FROM Products;",
    3: "SELECT * FROM Customers WHERE city = 'Cairo';",
    4: "SELECT * FROM Products ORDER BY unit_price DESC;",
    5: "SELECT * FROM Products ORDER BY unit_price DESC LIMIT 5;",

    # --------------------------
    # JOIN
    # --------------------------
    6: "SELECT c.customer_name, o.order_date FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id;",
    7: "SELECT p.product_name, s.supplier_name FROM Products p JOIN Suppliers s ON p.supplier_id = s.supplier_id;",
    8: "SELECT p.product_name, c.category_name FROM Products p JOIN Categories c ON p.category_id = c.category_id;",
    9: "SELECT DISTINCT c.customer_name, pay.payment_method FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id JOIN Payments pay ON o.payment_id = pay.payment_id;",

    # --------------------------
    # AGGREGATION
    # --------------------------
    10: "SELECT COUNT(*) FROM Customers;",
    11: "SELECT SUM(total_amount) FROM Orders;",
    12: "SELECT AVG(total_amount) FROM Orders;",
    13: "SELECT c.customer_name, SUM(o.total_amount) AS total_sales FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name;",
    14: "SELECT c.customer_name, COUNT(o.order_id) AS order_count FROM Customers c JOIN Orders o ON c.customer_id = o.customer_id GROUP BY c.customer_id, c.customer_name HAVING COUNT(o.order_id) > 5;",

    # --------------------------
    # SUBQUERY
    # --------------------------
    15: "SELECT * FROM Products WHERE unit_price = (SELECT MAX(unit_price) FROM Products);",
    16: (
        "WITH customer_totals AS ("
        "SELECT customer_id, SUM(total_amount) AS total_spent FROM Orders GROUP BY customer_id"
        ") "
        "SELECT c.customer_name, ct.total_spent FROM Customers c "
        "JOIN customer_totals ct ON c.customer_id = ct.customer_id "
        "WHERE ct.total_spent > (SELECT AVG(total_spent) FROM customer_totals);"
    ),

    # --------------------------
    # DATE
    # --------------------------
    17: "SELECT * FROM Orders WHERE strftime('%Y', order_date) = '2024';",
    18: "SELECT * FROM Orders WHERE strftime('%m', order_date) = '01';",

    # --------------------------
    # NULL
    # --------------------------
    19: "SELECT * FROM Customers c WHERE NOT EXISTS (SELECT 1 FROM Orders o WHERE o.customer_id = c.customer_id);",

    # --------------------------
    # CTE
    # --------------------------
    20: (
        "WITH customer_totals AS ("
        "SELECT customer_id, SUM(total_amount) AS total_spent FROM Orders GROUP BY customer_id"
        ") "
        "SELECT c.customer_name, ct.total_spent FROM Customers c "
        "JOIN customer_totals ct ON c.customer_id = ct.customer_id "
        "ORDER BY ct.total_spent DESC LIMIT 5;"
    ),

    # --------------------------
    # WINDOW
    # --------------------------
    21: (
        "WITH product_sales AS ("
        "SELECT product_id, SUM(quantity * unit_price * (1 - discount)) AS total_sales "
        "FROM Order_Items GROUP BY product_id"
        ") "
        "SELECT p.product_name, ps.total_sales, "
        "RANK() OVER (ORDER BY ps.total_sales DESC) AS sales_rank "
        "FROM Products p JOIN product_sales ps ON p.product_id = ps.product_id;"
    ),

    # --------------------------
    # IMPOSSIBLE
    # --------------------------
    22: REFUSAL_TOKEN,
    23: REFUSAL_TOKEN,
    24: REFUSAL_TOKEN,

    # ============================================================
    # NEW (v2)
    # ============================================================

    # --------------------------
    # DISTINCT
    # --------------------------
    25: "SELECT DISTINCT city FROM Customers;",
    26: "SELECT DISTINCT country FROM Suppliers;",
    27: "SELECT DISTINCT order_status FROM Orders;",

    # --------------------------
    # LEFT JOIN
    # --------------------------
    28: "SELECT c.customer_name, o.order_id FROM Customers c LEFT JOIN Orders o ON c.customer_id = o.customer_id;",
    29: "SELECT p.product_name, r.rating FROM Products p LEFT JOIN Reviews r ON p.product_id = r.product_id;",
    30: "SELECT s.supplier_name, p.product_name FROM Suppliers s LEFT JOIN Products p ON s.supplier_id = p.supplier_id;",
    31: (
        "SELECT cat.category_name, COUNT(p.product_id) AS product_count "
        "FROM Categories cat LEFT JOIN Products p ON cat.category_id = p.category_id "
        "GROUP BY cat.category_id, cat.category_name;"
    ),

    # --------------------------
    # GROUP BY
    # --------------------------
    32: "SELECT c.category_name, COUNT(p.product_id) AS product_count FROM Categories c JOIN Products p ON c.category_id = p.category_id GROUP BY c.category_id, c.category_name;",
    33: "SELECT product_id, SUM(quantity) AS total_quantity FROM Order_Items GROUP BY product_id;",
    34: "SELECT sh.company_name, COUNT(o.order_id) AS order_count FROM Shippers sh JOIN Orders o ON sh.shipper_id = o.shipper_id GROUP BY sh.shipper_id, sh.company_name;",
    35: "SELECT product_id, AVG(rating) AS avg_rating FROM Reviews GROUP BY product_id;",
    36: "SELECT country, COUNT(*) AS customer_count FROM Customers GROUP BY country;",

    # --------------------------
    # HAVING
    # --------------------------
    37: "SELECT product_id, SUM(quantity) AS total_quantity FROM Order_Items GROUP BY product_id HAVING SUM(quantity) > 10;",
    38: (
        "SELECT c.category_name, COUNT(p.product_id) AS product_count "
        "FROM Categories c JOIN Products p ON c.category_id = p.category_id "
        "GROUP BY c.category_id, c.category_name HAVING COUNT(p.product_id) > 3;"
    ),
    39: (
        "SELECT s.supplier_name, COUNT(p.product_id) AS product_count "
        "FROM Suppliers s JOIN Products p ON s.supplier_id = p.supplier_id "
        "GROUP BY s.supplier_id, s.supplier_name HAVING COUNT(p.product_id) > 2;"
    ),
    40: (
        "SELECT p.product_name, AVG(r.rating) AS avg_rating "
        "FROM Products p JOIN Reviews r ON p.product_id = r.product_id "
        "GROUP BY p.product_id, p.product_name HAVING AVG(r.rating) < 3;"
    ),

    # --------------------------
    # COUNT
    # --------------------------
    41: "SELECT COUNT(*) FROM Products;",
    42: "SELECT customer_id, COUNT(*) AS order_count FROM Orders GROUP BY customer_id;",
    43: "SELECT COUNT(*) FROM Products WHERE discontinued = 1;",
    44: "SELECT product_id, COUNT(*) AS review_count FROM Reviews GROUP BY product_id;",

    # --------------------------
    # SUM
    # --------------------------
    45: "SELECT SUM(stock_quantity) FROM Products;",
    46: "SELECT sh.company_name, SUM(o.total_amount) AS total_revenue FROM Shippers sh JOIN Orders o ON sh.shipper_id = o.shipper_id GROUP BY sh.shipper_id, sh.company_name;",
    47: "SELECT warehouse, SUM(quantity) AS total_quantity FROM Inventory GROUP BY warehouse;",
    48: (
        "SELECT e.employee_id, e.first_name, e.last_name, SUM(o.total_amount) AS total_sales "
        "FROM Employees e JOIN Orders o ON e.employee_id = o.employee_id "
        "GROUP BY e.employee_id, e.first_name, e.last_name;"
    ),

    # --------------------------
    # AVG
    # --------------------------
    49: "SELECT AVG(unit_price) FROM Products;",
    50: "SELECT product_id, ROUND(AVG(rating), 1) AS avg_rating FROM Reviews GROUP BY product_id;",
    51: "SELECT AVG(item_count) FROM (SELECT order_id, COUNT(*) AS item_count FROM Order_Items GROUP BY order_id);",

    # --------------------------
    # MIN / MAX
    # --------------------------
    52: "SELECT MAX(total_amount) FROM Orders;",
    53: [
        "SELECT * FROM Products ORDER BY unit_price ASC LIMIT 1;",
        "SELECT * FROM Products WHERE unit_price = (SELECT MIN(unit_price) FROM Products);",
    ],
    54: "SELECT customer_id, MAX(order_date) AS last_order_date FROM Orders GROUP BY customer_id;",
    55: "SELECT MIN(hire_date) FROM Employees;",

    # --------------------------
    # CASE
    # --------------------------
    56: "SELECT product_name, unit_price, CASE WHEN unit_price > 500 THEN 'Expensive' ELSE 'Affordable' END AS price_label FROM Products;",
    57: (
        "SELECT order_id, total_amount, "
        "CASE WHEN total_amount > 1000 THEN 'Large' "
        "WHEN total_amount >= 200 THEN 'Medium' "
        "ELSE 'Small' END AS order_size "
        "FROM Orders;"
    ),
    58: "SELECT product_name, stock_quantity, CASE WHEN stock_quantity > 0 THEN 'In Stock' ELSE 'Out of Stock' END AS stock_status FROM Products;",

    # --------------------------
    # SUBQUERY
    # --------------------------
    59: "SELECT * FROM Products WHERE unit_price > (SELECT AVG(unit_price) FROM Products);",
    60: (
        "SELECT c.customer_name FROM Customers c "
        "JOIN Orders o ON c.customer_id = o.customer_id "
        "WHERE o.total_amount = (SELECT MAX(total_amount) FROM Orders);"
    ),
    61: "SELECT * FROM Products WHERE product_id NOT IN (SELECT product_id FROM Order_Items);",
    62: (
        "SELECT s.supplier_name FROM Suppliers s "
        "WHERE (SELECT AVG(p.unit_price) FROM Products p WHERE p.supplier_id = s.supplier_id) "
        "> (SELECT AVG(unit_price) FROM Products);"
    ),
    63: "SELECT * FROM Products ORDER BY unit_price DESC LIMIT 1 OFFSET 1;",

    # --------------------------
    # EXISTS
    # --------------------------
    64: "SELECT * FROM Customers c WHERE EXISTS (SELECT 1 FROM Orders o WHERE o.customer_id = c.customer_id);",
    65: "SELECT * FROM Products p WHERE EXISTS (SELECT 1 FROM Reviews r WHERE r.product_id = p.product_id);",
    66: "SELECT * FROM Suppliers s WHERE EXISTS (SELECT 1 FROM Products p WHERE p.supplier_id = s.supplier_id AND p.discontinued = 1);",

    # --------------------------
    # NOT EXISTS
    # --------------------------
    67: "SELECT * FROM Products p WHERE NOT EXISTS (SELECT 1 FROM Reviews r WHERE r.product_id = p.product_id);",
    68: "SELECT * FROM Suppliers s WHERE NOT EXISTS (SELECT 1 FROM Products p WHERE p.supplier_id = s.supplier_id AND p.discontinued = 1);",

    # --------------------------
    # IN
    # --------------------------
    69: "SELECT o.* FROM Orders o JOIN Shippers sh ON o.shipper_id = sh.shipper_id WHERE sh.company_name IN ('Nile Express', 'Speedy Logistics');",
    70: "SELECT * FROM Customers WHERE country IN ('Egypt', 'UAE', 'Saudi Arabia');",
    71: "SELECT p.* FROM Products p JOIN Categories c ON p.category_id = c.category_id WHERE c.category_name IN ('Electronics', 'Books');",

    # --------------------------
    # UNION
    # --------------------------
    72: "SELECT city FROM Customers UNION SELECT city FROM Addresses;",
    73: "SELECT country FROM Customers UNION SELECT country FROM Suppliers UNION SELECT country FROM Addresses;",

    # --------------------------
    # CTE
    # --------------------------
    74: (
        "WITH category_revenue AS ("
        "SELECT p.category_id, SUM(oi.quantity * oi.unit_price * (1 - oi.discount)) AS revenue "
        "FROM Order_Items oi JOIN Products p ON oi.product_id = p.product_id "
        "GROUP BY p.category_id"
        ") "
        "SELECT c.category_name, cr.revenue FROM Categories c "
        "JOIN category_revenue cr ON c.category_id = cr.category_id;"
    ),
    75: (
        "WITH customer_totals AS ("
        "SELECT customer_id, SUM(total_amount) AS total_spent FROM Orders GROUP BY customer_id"
        ") "
        "SELECT c.customer_name, ct.total_spent FROM Customers c "
        "JOIN customer_totals ct ON c.customer_id = ct.customer_id "
        "WHERE ct.total_spent > 2000;"
    ),
    76: (
        "WITH employee_orders AS ("
        "SELECT employee_id, AVG(total_amount) AS avg_order_value FROM Orders GROUP BY employee_id"
        ") "
        "SELECT e.first_name, e.last_name, eo.avg_order_value FROM Employees e "
        "JOIN employee_orders eo ON e.employee_id = eo.employee_id;"
    ),

    # --------------------------
    # WINDOW
    # --------------------------
    77: (
        "SELECT customer_id, order_id, order_date, total_amount, "
        "SUM(total_amount) OVER (PARTITION BY customer_id ORDER BY order_date) AS running_total "
        "FROM Orders;"
    ),
    78: (
        "SELECT product_name, category_id, unit_price, "
        "RANK() OVER (PARTITION BY category_id ORDER BY unit_price DESC) AS price_rank "
        "FROM Products;"
    ),
    79: (
        "SELECT order_id, customer_id, total_amount, "
        "AVG(total_amount) OVER (PARTITION BY customer_id) AS customer_avg "
        "FROM Orders;"
    ),

    # --------------------------
    # DATE
    # --------------------------
    80: "SELECT * FROM Orders WHERE shipped_date IS NOT NULL AND julianday(shipped_date) - julianday(order_date) <= 5;",
    81: "SELECT * FROM Employees WHERE hire_date >= date('now', '-2 years');",
    82: "SELECT strftime('%Y-%m', order_date) AS month, COUNT(*) AS order_count FROM Orders GROUP BY month ORDER BY month;",
    83: "SELECT * FROM Orders WHERE order_date >= date('now', '-30 days');",

    # --------------------------
    # NULL
    # --------------------------
    84: "SELECT * FROM Orders WHERE shipped_date IS NULL;",
    85: "SELECT * FROM Customers WHERE email IS NULL;",
    86: "SELECT * FROM Products WHERE category_id IS NULL;",
    87: "SELECT order_id, COALESCE(employee_id, 'Unassigned') AS employee_id FROM Orders;",

    # --------------------------
    # IMPOSSIBLE
    # --------------------------
    88: REFUSAL_TOKEN,
    89: REFUSAL_TOKEN,
    90: REFUSAL_TOKEN,
    91: REFUSAL_TOKEN,

}