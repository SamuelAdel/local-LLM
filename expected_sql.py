"""
Reference SQL answers.
"""

EXPECTED_SQL = {

1:
"""
SELECT *
FROM Customers;
""",

2:
"""
SELECT *
FROM Products;
""",

3:
"""
SELECT *
FROM Customers
WHERE city='Cairo';
""",

4:
"""
SELECT *
FROM Products
ORDER BY unit_price DESC;
""",

5:
"""
SELECT *
FROM Products
ORDER BY unit_price DESC
LIMIT 5;
""",

6:
"""
SELECT
c.customer_name,
o.order_date
FROM Customers c
JOIN Orders o
ON c.customer_id=o.customer_id;
""",

7:
"""
SELECT
p.product_name,
s.supplier_name
FROM Products p
JOIN Suppliers s
ON p.supplier_id=s.supplier_id;
""",

8:
"""
SELECT
p.product_name,
c.category_name
FROM Products p
JOIN Categories c
ON p.category_id=c.category_id;
""",

9:
"""
SELECT
c.customer_name,
p.payment_method
FROM Customers c
JOIN Orders o
ON c.customer_id=o.customer_id
JOIN Payments p
ON o.payment_id=p.payment_id;
""",

10:
"""
SELECT COUNT(*)
FROM Customers;
""",

11:
"""
SELECT SUM(total_amount)
FROM Orders;
""",

12:
"""
SELECT AVG(total_amount)
FROM Orders;
""",

13:
"""
SELECT
customer_id,
SUM(total_amount)
FROM Orders
GROUP BY customer_id;
""",

14:
"""
SELECT
customer_id,
COUNT(*)
FROM Orders
GROUP BY customer_id
HAVING COUNT(*)>5;
""",

15:
"""
SELECT *
FROM Products
WHERE unit_price=(
SELECT MAX(unit_price)
FROM Products
);
""",

16:
"""
SELECT customer_id
FROM Orders
GROUP BY customer_id
HAVING SUM(total_amount) >
(
SELECT AVG(customer_total)
FROM
(
SELECT SUM(total_amount) customer_total
FROM Orders
GROUP BY customer_id
)t
);
""",

17:
"""
SELECT *
FROM Orders
WHERE YEAR(order_date)=2024;
""",

18:
"""
SELECT *
FROM Orders
WHERE MONTH(order_date)=1;
""",

19:
"""
SELECT *
FROM Customers
WHERE customer_id NOT IN
(
SELECT customer_id
FROM Orders
);
""",

20:
"""
WITH CustomerSales AS
(
SELECT
customer_id,
SUM(total_amount) total_sales
FROM Orders
GROUP BY customer_id
)
SELECT *
FROM CustomerSales
ORDER BY total_sales DESC
LIMIT 5;
""",

21:
"""
SELECT
product_id,
SUM(quantity) total_quantity,
RANK() OVER(
ORDER BY SUM(quantity) DESC
) ranking
FROM Order_Items
GROUP BY product_id;
""",

22:"CANNOT_GENERATE_SQL",

23:"CANNOT_GENERATE_SQL",

24:"CANNOT_GENERATE_SQL"

}