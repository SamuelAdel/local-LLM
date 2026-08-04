"""
create_database.py

Creates enterprise.db (SQLite) with tables matching the structure
described in schema.py. Run this before seed_database.py.

Usage:
    python create_database.py
"""

import sqlite3
import os

DB_PATH = "enterprise.db"

CREATE_STATEMENTS = [
    """
    CREATE TABLE Customers (
        customer_id INTEGER PRIMARY KEY,
        customer_name VARCHAR NOT NULL,
        email VARCHAR,
        phone VARCHAR,
        city VARCHAR,
        country VARCHAR,
        created_at DATE
    );
    """,
    """
    CREATE TABLE Addresses (
        address_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        street VARCHAR,
        city VARCHAR,
        state VARCHAR,
        postal_code VARCHAR,
        country VARCHAR,
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );
    """,
    """
    CREATE TABLE Categories (
        category_id INTEGER PRIMARY KEY,
        category_name VARCHAR NOT NULL
    );
    """,
    """
    CREATE TABLE Suppliers (
        supplier_id INTEGER PRIMARY KEY,
        supplier_name VARCHAR NOT NULL,
        country VARCHAR
    );
    """,
    """
    CREATE TABLE Products (
        product_id INTEGER PRIMARY KEY,
        product_name VARCHAR NOT NULL,
        category_id INTEGER,
        supplier_id INTEGER,
        unit_price DECIMAL,
        stock_quantity INTEGER,
        discontinued BOOLEAN,
        FOREIGN KEY (category_id) REFERENCES Categories(category_id),
        FOREIGN KEY (supplier_id) REFERENCES Suppliers(supplier_id)
    );
    """,
    """
    CREATE TABLE Employees (
        employee_id INTEGER PRIMARY KEY,
        first_name VARCHAR,
        last_name VARCHAR,
        title VARCHAR,
        hire_date DATE
    );
    """,
    """
    CREATE TABLE Shippers (
        shipper_id INTEGER PRIMARY KEY,
        company_name VARCHAR NOT NULL,
        phone VARCHAR
    );
    """,
    """
    CREATE TABLE Payments (
        payment_id INTEGER PRIMARY KEY,
        payment_method VARCHAR,
        payment_date DATE,
        payment_status VARCHAR
    );
    """,
    """
    CREATE TABLE Orders (
        order_id INTEGER PRIMARY KEY,
        customer_id INTEGER,
        employee_id INTEGER,
        shipper_id INTEGER,
        payment_id INTEGER,
        order_date DATE,
        shipped_date DATE,
        order_status VARCHAR,
        total_amount DECIMAL,
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id),
        FOREIGN KEY (employee_id) REFERENCES Employees(employee_id),
        FOREIGN KEY (shipper_id) REFERENCES Shippers(shipper_id),
        FOREIGN KEY (payment_id) REFERENCES Payments(payment_id)
    );
    """,
    """
    CREATE TABLE Order_Items (
        order_item_id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        unit_price DECIMAL,
        discount DECIMAL,
        FOREIGN KEY (order_id) REFERENCES Orders(order_id),
        FOREIGN KEY (product_id) REFERENCES Products(product_id)
    );
    """,
    """
    CREATE TABLE Inventory (
        inventory_id INTEGER PRIMARY KEY,
        product_id INTEGER,
        warehouse VARCHAR,
        quantity INTEGER,
        FOREIGN KEY (product_id) REFERENCES Products(product_id)
    );
    """,
    """
    CREATE TABLE Reviews (
        review_id INTEGER PRIMARY KEY,
        product_id INTEGER,
        customer_id INTEGER,
        rating INTEGER,
        review_date DATE,
        FOREIGN KEY (product_id) REFERENCES Products(product_id),
        FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
    );
    """,
]


def create_database(db_path: str = DB_PATH, overwrite: bool = True) -> None:
    if overwrite and os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")

    for statement in CREATE_STATEMENTS:
        cur.execute(statement)

    conn.commit()
    conn.close()
    print(f"[OK] Created '{db_path}' with {len(CREATE_STATEMENTS)} tables.")


if __name__ == "__main__":
    create_database()
