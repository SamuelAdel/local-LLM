"""
Evaluation benchmark questions.
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
}

]