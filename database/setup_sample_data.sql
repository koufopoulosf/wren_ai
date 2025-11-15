-- Sample Data Setup for Wren AI
-- This creates a simple e-commerce schema with sample data

-- Clean up existing tables (if any)
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS customers CASCADE;

-- Customers table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    country VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    category VARCHAR(50) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order Items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample customers
INSERT INTO customers (name, email, country) VALUES
('John Smith', 'john.smith@email.com', 'USA'),
('Emma Johnson', 'emma.j@email.com', 'Canada'),
('Michael Chen', 'michael.chen@email.com', 'USA'),
('Sarah Williams', 'sarah.w@email.com', 'UK'),
('David Brown', 'david.b@email.com', 'USA'),
('Lisa Anderson', 'lisa.a@email.com', 'Canada'),
('Robert Taylor', 'robert.t@email.com', 'UK'),
('Jennifer Martinez', 'jennifer.m@email.com', 'USA'),
('William Garcia', 'william.g@email.com', 'Canada'),
('Maria Rodriguez', 'maria.r@email.com', 'USA');

-- Insert sample products
INSERT INTO products (name, category, price, stock_quantity) VALUES
('Laptop Pro 15"', 'Electronics', 1299.99, 45),
('Wireless Mouse', 'Electronics', 29.99, 150),
('USB-C Cable', 'Electronics', 12.99, 300),
('Office Chair Deluxe', 'Furniture', 299.99, 30),
('Standing Desk', 'Furniture', 599.99, 15),
('Monitor 27"', 'Electronics', 349.99, 60),
('Keyboard Mechanical', 'Electronics', 89.99, 80),
('Desk Lamp LED', 'Furniture', 39.99, 100),
('Notebook Pack (5)', 'Office Supplies', 9.99, 500),
('Pen Set Premium', 'Office Supplies', 19.99, 200),
('Webcam HD', 'Electronics', 79.99, 40),
('Headphones Wireless', 'Electronics', 149.99, 70),
('Phone Stand', 'Furniture', 24.99, 120),
('Cable Organizer', 'Office Supplies', 14.99, 180),
('Ergonomic Mouse Pad', 'Office Supplies', 19.99, 150);

-- Insert sample orders (last 3 months)
INSERT INTO orders (customer_id, order_date, total_amount, status) VALUES
(1, CURRENT_DATE - INTERVAL '5 days', 1329.98, 'delivered'),
(2, CURRENT_DATE - INTERVAL '7 days', 349.99, 'delivered'),
(3, CURRENT_DATE - INTERVAL '10 days', 89.99, 'delivered'),
(4, CURRENT_DATE - INTERVAL '12 days', 1949.97, 'delivered'),
(5, CURRENT_DATE - INTERVAL '15 days', 29.99, 'delivered'),
(1, CURRENT_DATE - INTERVAL '20 days', 599.99, 'delivered'),
(6, CURRENT_DATE - INTERVAL '25 days', 379.98, 'delivered'),
(7, CURRENT_DATE - INTERVAL '30 days', 149.99, 'delivered'),
(8, CURRENT_DATE - INTERVAL '35 days', 1299.99, 'delivered'),
(9, CURRENT_DATE - INTERVAL '40 days', 129.98, 'delivered'),
(10, CURRENT_DATE - INTERVAL '45 days', 299.99, 'delivered'),
(2, CURRENT_DATE - INTERVAL '50 days', 79.99, 'delivered'),
(3, CURRENT_DATE - INTERVAL '55 days', 649.98, 'delivered'),
(4, CURRENT_DATE - INTERVAL '60 days', 39.99, 'delivered'),
(5, CURRENT_DATE - INTERVAL '65 days', 1329.98, 'delivered'),
(6, CURRENT_DATE - INTERVAL '70 days', 229.97, 'delivered'),
(7, CURRENT_DATE - INTERVAL '75 days', 349.99, 'delivered'),
(8, CURRENT_DATE - INTERVAL '80 days', 89.99, 'delivered'),
(9, CURRENT_DATE - INTERVAL '85 days', 599.99, 'delivered'),
(10, CURRENT_DATE - INTERVAL '90 days', 149.99, 'delivered');

-- Insert sample order items
INSERT INTO order_items (order_id, product_id, quantity, price) VALUES
-- Order 1
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99),
-- Order 2
(2, 6, 1, 349.99),
-- Order 3
(3, 7, 1, 89.99),
-- Order 4
(4, 1, 1, 1299.99),
(4, 5, 1, 599.99),
(4, 8, 1, 39.99),
-- Order 5
(5, 2, 1, 29.99),
-- Order 6
(6, 5, 1, 599.99),
-- Order 7
(7, 6, 1, 349.99),
(7, 2, 1, 29.99),
-- Order 8
(8, 12, 1, 149.99),
-- Order 9
(9, 1, 1, 1299.99),
-- Order 10
(10, 11, 1, 79.99),
(10, 8, 1, 39.99),
-- Order 11
(11, 4, 1, 299.99),
-- Order 12
(12, 11, 1, 79.99),
-- Order 13
(13, 5, 1, 599.99),
(13, 8, 1, 39.99),
-- Order 14
(14, 8, 1, 39.99),
-- Order 15
(15, 1, 1, 1299.99),
(15, 2, 1, 29.99),
-- Order 16
(16, 12, 1, 149.99),
(16, 11, 1, 79.99),
-- Order 17
(17, 6, 1, 349.99),
-- Order 18
(18, 7, 1, 89.99),
-- Order 19
(19, 5, 1, 599.99),
-- Order 20
(20, 12, 1, 149.99);

-- Verify data
SELECT 'Customers' AS table_name, COUNT(*) AS row_count FROM customers
UNION ALL
SELECT 'Products', COUNT(*) FROM products
UNION ALL
SELECT 'Orders', COUNT(*) FROM orders
UNION ALL
SELECT 'Order Items', COUNT(*) FROM order_items;

-- Show sample query results
SELECT
    'Sample Query: Top 5 customers by revenue' AS description,
    c.name,
    c.country,
    SUM(o.total_amount) AS total_revenue
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.country
ORDER BY total_revenue DESC
LIMIT 5;
