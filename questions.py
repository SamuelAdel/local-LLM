"""
Evaluation benchmark questions.

v2: expanded from 24 -> 91 questions to give a statistically meaningful
comparison across models and to cover every major SQL construct a
text-to-SQL model should be tested on, not just SELECT/JOIN/aggregation.

IDs 1-24 are unchanged from v1 (same id, category, difficulty, question
text) so any already-collected results/<model>.txt files stay valid and
main.py's per-question resume logic keeps working without re-running
those questions. IDs 25+ are new.

Category coverage added in this pass: DISTINCT, LEFT JOIN, more
GROUP BY / HAVING / COUNT / SUM / AVG / MIN / MAX, CASE, more SUBQUERY,
EXISTS, NOT EXISTS, IN, UNION, more CTE, more WINDOW, more DATE, NULL
handling, and more IMPOSSIBLE (refusal) cases.

Note on RIGHT JOIN: intentionally not included. SQLite only added RIGHT
JOIN support in 3.39 (2022); relying on it makes the benchmark's gold
answers environment-fragile, and LEFT JOIN already exercises the same
"preserve unmatched rows" reasoning a model needs to demonstrate.
"""

QUESTIONS = [

# --------------------------
# SIMPLE SELECT
# --------------------------

{
"id":1,
"category":"SELECT",
"difficulty":"Easy",
"question":"List all customers."
},

{
"id":2,
"category":"SELECT",
"difficulty":"Easy",
"question":"List all products."
},

{
"id":3,
"category":"FILTER",
"difficulty":"Easy",
"question":"Show customers who live in Cairo."
},

{
"id":4,
"category":"ORDER BY",
"difficulty":"Easy",
"question":"Show products ordered by price descending."
},

{
"id":5,
"category":"LIMIT",
"difficulty":"Easy",
"question":"Show the five most expensive products."
},

# --------------------------
# JOIN
# --------------------------

{
"id":6,
"category":"JOIN",
"difficulty":"Medium",
"question":"List customer names with their order dates."
},

{
"id":7,
"category":"JOIN",
"difficulty":"Medium",
"question":"List product names with supplier names."
},

{
"id":8,
"category":"JOIN",
"difficulty":"Medium",
"question":"Show products with category names."
},

{
"id":9,
"category":"JOIN",
"difficulty":"Medium",
"question":"List customer names and payment methods."
},

# --------------------------
# AGGREGATION
# --------------------------

{
"id":10,
"category":"COUNT",
"difficulty":"Easy",
"question":"How many customers are there?"
},

{
"id":11,
"category":"SUM",
"difficulty":"Medium",
"question":"Calculate total sales."
},

{
"id":12,
"category":"AVG",
"difficulty":"Medium",
"question":"Calculate average order amount."
},

{
"id":13,
"category":"GROUP BY",
"difficulty":"Medium",
"question":"Show total sales for each customer."
},

{
"id":14,
"category":"HAVING",
"difficulty":"Hard",
"question":"Show customers with more than five orders."
},

# --------------------------
# SUBQUERY
# --------------------------

{
"id":15,
"category":"SUBQUERY",
"difficulty":"Hard",
"question":"Show the most expensive product."
},

{
"id":16,
"category":"SUBQUERY",
"difficulty":"Hard",
"question":"Show customers whose total spending is above the average customer spending."
},

# --------------------------
# DATE
# --------------------------

{
"id":17,
"category":"DATE",
"difficulty":"Medium",
"question":"Show orders placed in 2024."
},

{
"id":18,
"category":"DATE",
"difficulty":"Medium",
"question":"Show orders placed during January."
},

# --------------------------
# NULL
# --------------------------

{
"id":19,
"category":"NULL",
"difficulty":"Hard",
"question":"Show customers who never placed an order."
},

# --------------------------
# CTE
# --------------------------

{
"id":20,
"category":"CTE",
"difficulty":"Expert",
"question":"Find the top five customers by total spending."
},

# --------------------------
# WINDOW
# --------------------------

{
"id":21,
"category":"WINDOW",
"difficulty":"Expert",
"question":"Rank products by total sales."
},

# --------------------------
# IMPOSSIBLE
# --------------------------

{
"id":22,
"category":"IMPOSSIBLE",
"difficulty":"Easy",
"question":"Show employee salaries."
},

{
"id":23,
"category":"IMPOSSIBLE",
"difficulty":"Easy",
"question":"Show customer birthdays."
},

{
"id":24,
"category":"IMPOSSIBLE",
"difficulty":"Easy",
"question":"Show product colors."
},

# ============================================================
# NEW QUESTIONS (v2) -- ids 25+
# ============================================================

# --------------------------
# DISTINCT
# --------------------------

{
"id":25,
"category":"DISTINCT",
"difficulty":"Easy",
"question":"List all distinct cities where customers live."
},

{
"id":26,
"category":"DISTINCT",
"difficulty":"Medium",
"question":"List all distinct countries suppliers come from."
},

{
"id":27,
"category":"DISTINCT",
"difficulty":"Medium",
"question":"List the distinct order statuses used in the Orders table."
},

# --------------------------
# LEFT JOIN
# --------------------------

{
"id":28,
"category":"LEFT JOIN",
"difficulty":"Medium",
"question":"List all customers with their orders, including customers who have no orders."
},

{
"id":29,
"category":"LEFT JOIN",
"difficulty":"Medium",
"question":"List all products with their reviews, including products with no reviews."
},

{
"id":30,
"category":"LEFT JOIN",
"difficulty":"Medium",
"question":"Show all suppliers along with their products, including suppliers with no products."
},

{
"id":31,
"category":"LEFT JOIN",
"difficulty":"Hard",
"question":"List categories along with the number of products in each, including categories with zero products."
},

# --------------------------
# GROUP BY
# --------------------------

{
"id":32,
"category":"GROUP BY",
"difficulty":"Medium",
"question":"Show the number of products in each category."
},

{
"id":33,
"category":"GROUP BY",
"difficulty":"Medium",
"question":"Show total quantity sold for each product."
},

{
"id":34,
"category":"GROUP BY",
"difficulty":"Medium",
"question":"Show the number of orders placed through each shipper."
},

{
"id":35,
"category":"GROUP BY",
"difficulty":"Hard",
"question":"Show the average rating for each product."
},

{
"id":36,
"category":"GROUP BY",
"difficulty":"Medium",
"question":"Show the number of customers in each country."
},

# --------------------------
# HAVING
# --------------------------

{
"id":37,
"category":"HAVING",
"difficulty":"Hard",
"question":"Show products that have been ordered more than ten units in total."
},

{
"id":38,
"category":"HAVING",
"difficulty":"Hard",
"question":"Show categories that contain more than three products."
},

{
"id":39,
"category":"HAVING",
"difficulty":"Medium",
"question":"Show suppliers who supply more than two products."
},

{
"id":40,
"category":"HAVING",
"difficulty":"Hard",
"question":"Show products with an average review rating below 3."
},

# --------------------------
# COUNT
# --------------------------

{
"id":41,
"category":"COUNT",
"difficulty":"Easy",
"question":"How many products are there?"
},

{
"id":42,
"category":"COUNT",
"difficulty":"Easy",
"question":"How many orders has each customer placed?"
},

{
"id":43,
"category":"COUNT",
"difficulty":"Medium",
"question":"How many products are discontinued?"
},

{
"id":44,
"category":"COUNT",
"difficulty":"Medium",
"question":"How many reviews does each product have?"
},

# --------------------------
# SUM
# --------------------------

{
"id":45,
"category":"SUM",
"difficulty":"Medium",
"question":"Calculate total quantity in stock across all products."
},

{
"id":46,
"category":"SUM",
"difficulty":"Medium",
"question":"Calculate total revenue for each shipper."
},

{
"id":47,
"category":"SUM",
"difficulty":"Medium",
"question":"Calculate total inventory quantity per warehouse."
},

{
"id":48,
"category":"SUM",
"difficulty":"Hard",
"question":"Calculate total sales for each employee."
},

# --------------------------
# AVG
# --------------------------

{
"id":49,
"category":"AVG",
"difficulty":"Medium",
"question":"Calculate the average product price."
},

{
"id":50,
"category":"AVG",
"difficulty":"Medium",
"question":"Calculate the average rating for each product, rounded to one decimal place."
},

{
"id":51,
"category":"AVG",
"difficulty":"Hard",
"question":"Calculate the average number of items per order."
},

# --------------------------
# MIN / MAX
# --------------------------

{
"id":52,
"category":"MAX",
"difficulty":"Easy",
"question":"Show the highest order total amount."
},

{
"id":53,
"category":"MIN",
"difficulty":"Easy",
"question":"Show the cheapest product."
},

{
"id":54,
"category":"MAX",
"difficulty":"Medium",
"question":"Show the most recent order date for each customer."
},

{
"id":55,
"category":"MIN",
"difficulty":"Medium",
"question":"Show the earliest hire date among employees."
},

# --------------------------
# CASE
# --------------------------

{
"id":56,
"category":"CASE",
"difficulty":"Medium",
"question":"Label each product as 'Expensive' if its price is above 500, otherwise 'Affordable'."
},

{
"id":57,
"category":"CASE",
"difficulty":"Hard",
"question":"Label each order as 'Large' if its total is above 1000, 'Medium' if between 200 and 1000, otherwise 'Small'."
},

{
"id":58,
"category":"CASE",
"difficulty":"Medium",
"question":"Show each product with a stock status of 'In Stock' or 'Out of Stock'."
},

# --------------------------
# SUBQUERY
# --------------------------

{
"id":59,
"category":"SUBQUERY",
"difficulty":"Hard",
"question":"Show products priced above the average product price."
},

{
"id":60,
"category":"SUBQUERY",
"difficulty":"Hard",
"question":"Show the customer who placed the largest single order."
},

{
"id":61,
"category":"SUBQUERY",
"difficulty":"Hard",
"question":"Show products that have never been ordered."
},

{
"id":62,
"category":"SUBQUERY",
"difficulty":"Expert",
"question":"Show suppliers whose average product price is higher than the overall average product price."
},

{
"id":63,
"category":"SUBQUERY",
"difficulty":"Hard",
"question":"Show the second most expensive product."
},

# --------------------------
# EXISTS
# --------------------------

{
"id":64,
"category":"EXISTS",
"difficulty":"Hard",
"question":"Show customers who have placed at least one order."
},

{
"id":65,
"category":"EXISTS",
"difficulty":"Hard",
"question":"Show products that have at least one review."
},

{
"id":66,
"category":"EXISTS",
"difficulty":"Expert",
"question":"Show suppliers that have at least one discontinued product."
},

# --------------------------
# NOT EXISTS
# --------------------------

{
"id":67,
"category":"NOT EXISTS",
"difficulty":"Hard",
"question":"Show products that have never received a review."
},

{
"id":68,
"category":"NOT EXISTS",
"difficulty":"Expert",
"question":"Show suppliers who have no discontinued products."
},

# --------------------------
# IN
# --------------------------

{
"id":69,
"category":"IN",
"difficulty":"Medium",
"question":"Show orders that were shipped by 'Nile Express' or 'Speedy Logistics'."
},

{
"id":70,
"category":"IN",
"difficulty":"Medium",
"question":"Show customers who live in Egypt, UAE, or Saudi Arabia."
},

{
"id":71,
"category":"IN",
"difficulty":"Medium",
"question":"Show products that belong to the 'Electronics' or 'Books' categories."
},

# --------------------------
# UNION
# --------------------------

{
"id":72,
"category":"UNION",
"difficulty":"Hard",
"question":"List all cities that appear in either the Customers table or the Addresses table."
},

{
"id":73,
"category":"UNION",
"difficulty":"Expert",
"question":"List all distinct country names that appear among customers, suppliers, or addresses."
},

# --------------------------
# CTE
# --------------------------

{
"id":74,
"category":"CTE",
"difficulty":"Expert",
"question":"Using a CTE, show each category's total revenue from order items."
},

{
"id":75,
"category":"CTE",
"difficulty":"Expert",
"question":"Using a CTE, find customers who spent more than 2000 in total."
},

{
"id":76,
"category":"CTE",
"difficulty":"Expert",
"question":"Using a CTE, show the average order value per employee."
},

# --------------------------
# WINDOW
# --------------------------

{
"id":77,
"category":"WINDOW",
"difficulty":"Expert",
"question":"Show each customer's orders along with a running total of their spending, ordered by order date."
},

{
"id":78,
"category":"WINDOW",
"difficulty":"Expert",
"question":"Show each product with its price rank within its own category."
},

{
"id":79,
"category":"WINDOW",
"difficulty":"Expert",
"question":"For each order, show its total amount alongside the average order amount of the same customer, using a window function."
},

# --------------------------
# DATE
# --------------------------

{
"id":80,
"category":"DATE",
"difficulty":"Medium",
"question":"Show orders that were shipped within 5 days of being placed."
},

{
"id":81,
"category":"DATE",
"difficulty":"Medium",
"question":"Show employees hired in the last two years."
},

{
"id":82,
"category":"DATE",
"difficulty":"Hard",
"question":"Show the number of orders placed each month."
},

{
"id":83,
"category":"DATE",
"difficulty":"Medium",
"question":"Show orders placed in the last 30 days."
},

# --------------------------
# NULL
# --------------------------

{
"id":84,
"category":"NULL",
"difficulty":"Medium",
"question":"Show orders where the shipped date is null."
},

{
"id":85,
"category":"NULL",
"difficulty":"Hard",
"question":"Show customers who don't have an email address on file."
},

{
"id":86,
"category":"NULL",
"difficulty":"Medium",
"question":"Show products with a missing category assignment."
},

{
"id":87,
"category":"NULL",
"difficulty":"Hard",
"question":"Show each order's employee id, displaying 'Unassigned' instead of null when there is no employee assigned."
},

# --------------------------
# IMPOSSIBLE
# --------------------------

{
"id":88,
"category":"IMPOSSIBLE",
"difficulty":"Easy",
"question":"Show product manufacturing dates."
},

{
"id":89,
"category":"IMPOSSIBLE",
"difficulty":"Easy",
"question":"Show customer credit card numbers."
},

{
"id":90,
"category":"IMPOSSIBLE",
"difficulty":"Medium",
"question":"Show the profit margin for each product."
},

{
"id":91,
"category":"IMPOSSIBLE",
"difficulty":"Medium",
"question":"Show which employee restocked each inventory item."
},

]