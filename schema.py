"""
Database schema used during evaluation.
"""

DATABASE_SCHEMA = """
Tables:

Customers(
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR,
    email VARCHAR,
    phone VARCHAR,
    city VARCHAR,
    country VARCHAR,
    created_at DATE
)

Addresses(
    address_id INT PRIMARY KEY,
    customer_id INT,
    street VARCHAR,
    city VARCHAR,
    state VARCHAR,
    postal_code VARCHAR,
    country VARCHAR
)

Categories(
    category_id INT PRIMARY KEY,
    category_name VARCHAR
)

Suppliers(
    supplier_id INT PRIMARY KEY,
    supplier_name VARCHAR,
    country VARCHAR
)

Products(
    product_id INT PRIMARY KEY,
    product_name VARCHAR,
    category_id INT,
    supplier_id INT,
    unit_price DECIMAL,
    stock_quantity INT,
    discontinued BOOLEAN
)

Orders(
    order_id INT PRIMARY KEY,
    customer_id INT,
    employee_id INT,
    shipper_id INT,
    payment_id INT,
    order_date DATE,
    shipped_date DATE,
    order_status VARCHAR,
    total_amount DECIMAL
)

Order_Items(
    order_item_id INT PRIMARY KEY,
    order_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL,
    discount DECIMAL
)

Employees(
    employee_id INT PRIMARY KEY,
    first_name VARCHAR,
    last_name VARCHAR,
    title VARCHAR,
    hire_date DATE
)

Shippers(
    shipper_id INT PRIMARY KEY,
    company_name VARCHAR,
    phone VARCHAR
)

Payments(
    payment_id INT PRIMARY KEY,
    payment_method VARCHAR,
    payment_date DATE,
    payment_status VARCHAR
)

Inventory(
    inventory_id INT PRIMARY KEY,
    product_id INT,
    warehouse VARCHAR,
    quantity INT
)

Reviews(
    review_id INT PRIMARY KEY,
    product_id INT,
    customer_id INT,
    rating INT,
    review_date DATE
)
"""