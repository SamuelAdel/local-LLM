"""
prompts.py
----------
This file contains:

1. Database Schema used during evaluation.
2. Prompt template sent to the LLM.
3. Evaluation questions.

If you need to change the dataset or add new questions,
modify this file only.
"""

# ==========================================================
# Database Schema
# ==========================================================

DATABASE_SCHEMA = """
Tables:

Customers(
    customer_id,
    customer_name,
    city
)

Orders(
    order_id,
    customer_id,
    order_date,
    total_amount
)

Products(
    product_id,
    product_name,
    category,
    price
)

Order_Items(
    order_id,
    product_id,
    quantity
)
"""


# ==========================================================
# Prompt Template
# ==========================================================

PROMPT_TEMPLATE = """
You are an expert SQL developer.

Your task is to generate a correct SQL query based on the user's request.

Rules:
- Use ONLY the provided database schema.
- Do not invent tables or columns.
- Return ONLY the SQL query.
- Do not explain your answer.
- Do not use markdown.
- If the request cannot be answered using the schema, return:
  CANNOT_GENERATE_SQL

Database Schema:
{schema}

User Question:
{question}
"""