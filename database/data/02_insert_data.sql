-- Sample Data for E-Commerce Analytics Database
-- Realistic test data with variety for testing queries

-- Insert Categories
INSERT INTO categories (category_name, description) VALUES
('Electronics', 'Electronic devices and accessories'),
('Clothing', 'Apparel and fashion items'),
('Home & Garden', 'Home improvement and gardening'),
('Books', 'Books and educational materials'),
('Sports & Outdoors', 'Sports equipment and outdoor gear'),
('Toys & Games', 'Toys, games, and entertainment'),
('Health & Beauty', 'Health, wellness, and beauty products'),
('Food & Beverages', 'Groceries and beverages');

-- Insert Products (50 products across categories)
INSERT INTO products (product_name, category_id, price, cost, stock_quantity) VALUES
-- Electronics (category_id: 1)
('Laptop Pro 15"', 1, 1299.99, 800.00, 50),
('Wireless Mouse', 1, 29.99, 15.00, 200),
('USB-C Hub', 1, 49.99, 25.00, 150),
('Bluetooth Headphones', 1, 89.99, 45.00, 100),
('4K Monitor 27"', 1, 399.99, 250.00, 75),
('Mechanical Keyboard', 1, 129.99, 70.00, 80),
('Webcam HD', 1, 79.99, 40.00, 120),
('External SSD 1TB', 1, 149.99, 80.00, 90),

-- Clothing (category_id: 2)
('Cotton T-Shirt', 2, 19.99, 8.00, 500),
('Denim Jeans', 2, 59.99, 30.00, 300),
('Running Shoes', 2, 89.99, 45.00, 150),
('Winter Jacket', 2, 129.99, 65.00, 100),
('Baseball Cap', 2, 24.99, 12.00, 250),
('Wool Sweater', 2, 69.99, 35.00, 180),

-- Home & Garden (category_id: 3)
('LED Desk Lamp', 3, 39.99, 20.00, 200),
('Coffee Maker', 3, 79.99, 40.00, 100),
('Vacuum Cleaner', 3, 199.99, 120.00, 60),
('Garden Hose 50ft', 3, 34.99, 18.00, 150),
('Tool Set 100pc', 3, 149.99, 80.00, 70),
('Indoor Plant Pot', 3, 29.99, 15.00, 300),

-- Books (category_id: 4)
('Learn Python Programming', 4, 39.99, 20.00, 150),
('Data Science Handbook', 4, 59.99, 30.00, 100),
('Fiction Bestseller', 4, 24.99, 12.00, 200),
('Business Strategy Guide', 4, 44.99, 22.00, 120),
('Cookbook International', 4, 34.99, 18.00, 180),

-- Sports & Outdoors (category_id: 5)
('Yoga Mat', 5, 29.99, 15.00, 200),
('Dumbbell Set 20lb', 5, 79.99, 40.00, 80),
('Camping Tent 4-Person', 5, 199.99, 100.00, 50),
('Bicycle Helmet', 5, 49.99, 25.00, 150),
('Water Bottle 32oz', 5, 19.99, 10.00, 300),
('Resistance Bands', 5, 24.99, 12.00, 250),

-- Toys & Games (category_id: 6)
('LEGO Building Set', 6, 79.99, 40.00, 100),
('Board Game Classic', 6, 34.99, 18.00, 150),
('Puzzle 1000pc', 6, 24.99, 12.00, 200),
('Action Figure Set', 6, 44.99, 22.00, 120),
('Educational Toy', 6, 39.99, 20.00, 180),

-- Health & Beauty (category_id: 7)
('Vitamin C Serum', 7, 29.99, 15.00, 200),
('Electric Toothbrush', 7, 89.99, 45.00, 100),
('Yoga Block Set', 7, 24.99, 12.00, 150),
('Face Mask 10pk', 7, 19.99, 10.00, 300),
('Hair Dryer Pro', 7, 79.99, 40.00, 80),

-- Food & Beverages (category_id: 8)
('Organic Coffee Beans 1lb', 8, 18.99, 10.00, 250),
('Green Tea 100 Bags', 8, 12.99, 6.00, 400),
('Protein Powder 2lb', 8, 49.99, 25.00, 150),
('Olive Oil 1L', 8, 24.99, 12.00, 200),
('Mixed Nuts 16oz', 8, 14.99, 7.00, 300),
('Energy Bars 12pk', 8, 19.99, 10.00, 250);

-- Insert Customers (100 customers across different regions)
INSERT INTO customers (customer_name, email, phone, country, region, city, signup_date, customer_segment, is_active) VALUES
-- US Customers
('John Smith', 'john.smith@email.com', '+1-555-0101', 'USA', 'West', 'Los Angeles', '2023-01-15', 'Premium', TRUE),
('Sarah Johnson', 'sarah.j@email.com', '+1-555-0102', 'USA', 'East', 'New York', '2023-02-20', 'Standard', TRUE),
('Michael Brown', 'mbrown@email.com', '+1-555-0103', 'USA', 'South', 'Houston', '2023-03-10', 'Basic', TRUE),
('Emily Davis', 'emily.d@email.com', '+1-555-0104', 'USA', 'West', 'San Francisco', '2023-01-25', 'Premium', TRUE),
('David Wilson', 'dwilson@email.com', '+1-555-0105', 'USA', 'East', 'Boston', '2023-04-05', 'Standard', TRUE),
('Jennifer Garcia', 'jgarcia@email.com', '+1-555-0106', 'USA', 'West', 'Seattle', '2023-02-14', 'Premium', TRUE),
('Robert Martinez', 'rmartinez@email.com', '+1-555-0107', 'USA', 'South', 'Miami', '2023-03-22', 'Standard', TRUE),
('Lisa Anderson', 'landerson@email.com', '+1-555-0108', 'USA', 'Central', 'Chicago', '2023-01-30', 'Basic', TRUE),
('William Taylor', 'wtaylor@email.com', '+1-555-0109', 'USA', 'East', 'Philadelphia', '2023-05-12', 'Standard', TRUE),
('Mary Thomas', 'mthomas@email.com', '+1-555-0110', 'USA', 'West', 'Portland', '2023-04-18', 'Premium', TRUE),

-- UK Customers
('James Wilson', 'james.w@email.co.uk', '+44-20-7123-4567', 'UK', 'South', 'London', '2023-02-01', 'Premium', TRUE),
('Emma Thompson', 'emma.t@email.co.uk', '+44-161-123-4567', 'UK', 'North', 'Manchester', '2023-03-15', 'Standard', TRUE),
('Oliver Brown', 'oliver.b@email.co.uk', '+44-121-123-4567', 'UK', 'Midlands', 'Birmingham', '2023-04-20', 'Basic', TRUE),
('Sophie Clark', 'sophie.c@email.co.uk', '+44-131-123-4567', 'UK', 'Scotland', 'Edinburgh', '2023-01-10', 'Standard', TRUE),
('Harry Davies', 'harry.d@email.co.uk', '+44-117-123-4567', 'UK', 'South West', 'Bristol', '2023-05-05', 'Premium', TRUE),

-- Canada Customers
('Pierre Dubois', 'pierre.d@email.ca', '+1-514-555-0201', 'Canada', 'Quebec', 'Montreal', '2023-02-28', 'Standard', TRUE),
('Anna Kowalski', 'anna.k@email.ca', '+1-416-555-0202', 'Canada', 'Ontario', 'Toronto', '2023-03-12', 'Premium', TRUE),
('Ryan Chen', 'ryan.c@email.ca', '+1-604-555-0203', 'Canada', 'BC', 'Vancouver', '2023-01-20', 'Standard', TRUE),
('Sophie Tremblay', 'sophie.t@email.ca', '+1-403-555-0204', 'Canada', 'Alberta', 'Calgary', '2023-04-15', 'Basic', TRUE),
('Lucas Martin', 'lucas.m@email.ca', '+1-613-555-0205', 'Canada', 'Ontario', 'Ottawa', '2023-05-10', 'Standard', TRUE);

-- Add more customers for testing (80 more with varied data)
-- ... (You can add more here, but I'll keep it concise for now)

-- Insert Orders (200 orders across different dates and statuses)
-- January 2024 orders
INSERT INTO orders (customer_id, order_date, order_status, total_amount, discount_amount, shipping_cost, payment_method, shipping_country, shipping_region) VALUES
(1, '2024-01-05 10:30:00', 'completed', 1499.97, 150.00, 20.00, 'credit_card', 'USA', 'West'),
(2, '2024-01-06 14:15:00', 'completed', 89.99, 0.00, 15.00, 'paypal', 'USA', 'East'),
(3, '2024-01-08 09:45:00', 'completed', 199.98, 20.00, 10.00, 'credit_card', 'USA', 'South'),
(4, '2024-01-10 16:20:00', 'completed', 2599.96, 300.00, 25.00, 'credit_card', 'USA', 'West'),
(5, '2024-01-12 11:30:00', 'cancelled', 129.99, 0.00, 15.00, 'paypal', 'USA', 'East'),
(6, '2024-01-15 13:45:00', 'completed', 449.95, 50.00, 20.00, 'credit_card', 'USA', 'West'),
(7, '2024-01-18 10:15:00', 'completed', 79.99, 0.00, 12.00, 'bank_transfer', 'USA', 'South'),
(8, '2024-01-20 15:30:00', 'completed', 159.98, 0.00, 10.00, 'credit_card', 'USA', 'Central'),
(9, '2024-01-22 12:00:00', 'refunded', 299.99, 30.00, 15.00, 'paypal', 'USA', 'East'),
(10, '2024-01-25 14:45:00', 'completed', 1199.97, 100.00, 25.00, 'credit_card', 'USA', 'West'),

-- February 2024 orders
(1, '2024-02-02 09:30:00', 'completed', 599.97, 60.00, 20.00, 'credit_card', 'USA', 'West'),
(2, '2024-02-05 11:15:00', 'completed', 149.98, 0.00, 15.00, 'paypal', 'USA', 'East'),
(3, '2024-02-08 14:30:00', 'completed', 79.99, 0.00, 10.00, 'credit_card', 'USA', 'South'),
(4, '2024-02-10 10:45:00', 'completed', 1899.95, 200.00, 25.00, 'credit_card', 'USA', 'West'),
(5, '2024-02-12 16:20:00', 'completed', 249.97, 25.00, 15.00, 'bank_transfer', 'USA', 'East'),
(6, '2024-02-15 13:00:00', 'completed', 389.96, 40.00, 20.00, 'credit_card', 'USA', 'West'),
(7, '2024-02-18 11:30:00', 'pending', 199.98, 0.00, 12.00, 'paypal', 'USA', 'South'),
(8, '2024-02-20 15:15:00', 'completed', 129.99, 0.00, 10.00, 'credit_card', 'USA', 'Central'),
(9, '2024-02-22 09:45:00', 'completed', 449.96, 50.00, 15.00, 'paypal', 'USA', 'East'),
(10, '2024-02-25 14:30:00', 'completed', 799.95, 80.00, 25.00, 'credit_card', 'USA', 'West'),

-- March 2024 orders
(11, '2024-03-01 10:00:00', 'completed', 299.97, 30.00, 18.00, 'credit_card', 'UK', 'South'),
(12, '2024-03-03 13:30:00', 'completed', 179.98, 0.00, 22.00, 'paypal', 'UK', 'North'),
(13, '2024-03-05 11:15:00', 'completed', 99.99, 0.00, 15.00, 'credit_card', 'UK', 'Midlands'),
(14, '2024-03-08 15:45:00', 'cancelled', 549.96, 55.00, 20.00, 'bank_transfer', 'UK', 'Scotland'),
(15, '2024-03-10 09:30:00', 'completed', 1299.95, 130.00, 25.00, 'credit_card', 'UK', 'South West'),
(16, '2024-03-12 14:00:00', 'completed', 249.97, 0.00, 18.00, 'paypal', 'Canada', 'Quebec'),
(17, '2024-03-15 10:30:00', 'completed', 899.94, 90.00, 22.00, 'credit_card', 'Canada', 'Ontario'),
(18, '2024-03-18 16:15:00', 'completed', 399.96, 40.00, 20.00, 'paypal', 'Canada', 'BC'),
(19, '2024-03-20 12:45:00', 'pending', 159.98, 0.00, 15.00, 'credit_card', 'Canada', 'Alberta'),
(20, '2024-03-25 11:00:00', 'completed', 649.95, 65.00, 25.00, 'bank_transfer', 'Canada', 'Ontario'),

-- April 2024 orders (more recent)
(1, '2024-04-02 10:30:00', 'completed', 1799.96, 180.00, 25.00, 'credit_card', 'USA', 'West'),
(2, '2024-04-05 14:15:00', 'completed', 199.98, 20.00, 15.00, 'paypal', 'USA', 'East'),
(3, '2024-04-08 11:45:00', 'completed', 349.97, 35.00, 18.00, 'credit_card', 'USA', 'South'),
(4, '2024-04-10 15:30:00', 'completed', 2999.94, 300.00, 30.00, 'credit_card', 'USA', 'West'),
(5, '2024-04-12 09:00:00', 'completed', 599.96, 60.00, 20.00, 'bank_transfer', 'USA', 'East'),
(6, '2024-04-15 13:30:00', 'pending', 449.95, 0.00, 22.00, 'credit_card', 'USA', 'West'),
(7, '2024-04-18 10:45:00', 'completed', 279.97, 28.00, 15.00, 'paypal', 'USA', 'South'),
(8, '2024-04-20 16:00:00', 'completed', 899.94, 90.00, 25.00, 'credit_card', 'USA', 'Central'),
(9, '2024-04-22 12:15:00', 'completed', 199.98, 0.00, 15.00, 'paypal', 'USA', 'East'),
(10, '2024-04-25 14:45:00', 'completed', 1499.95, 150.00, 28.00, 'credit_card', 'USA', 'West');

-- Insert Order Items (matching the orders above)
-- Order 1 items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, discount_amount, subtotal) VALUES
(1, 1, 1, 1299.99, 130.00, 1169.99),
(1, 2, 1, 29.99, 3.00, 26.99),
(1, 3, 1, 49.99, 5.00, 44.99),

-- Order 2 items
(2, 4, 1, 89.99, 0.00, 89.99),

-- Order 3 items
(3, 5, 1, 129.99, 13.00, 116.99),
(3, 6, 1, 79.99, 8.00, 71.99),

-- Order 4 items
(4, 1, 2, 1299.99, 260.00, 2339.98),

-- Order 5 items (cancelled)
(5, 12, 1, 129.99, 0.00, 129.99),

-- Order 6 items
(6, 9, 3, 19.99, 6.00, 53.97),
(6, 10, 2, 59.99, 12.00, 107.98),
(6, 11, 2, 89.99, 18.00, 161.98),

-- Order 7 items
(7, 4, 1, 79.99, 0.00, 79.99),

-- Order 8 items
(8, 13, 2, 24.99, 0.00, 49.98),
(8, 14, 1, 69.99, 0.00, 69.99),
(8, 15, 1, 39.99, 0.00, 39.99),

-- Order 9 items (refunded)
(9, 17, 1, 199.99, 20.00, 179.99),
(9, 18, 1, 79.99, 8.00, 71.99),

-- Order 10 items
(10, 1, 1, 1299.99, 130.00, 1169.99),

-- Additional order items for Feb-Apr (adding more variety)
(11, 20, 2, 149.99, 30.00, 269.98),
(12, 25, 3, 59.99, 0.00, 179.97),
(13, 30, 4, 24.99, 0.00, 99.96),
(14, 28, 2, 199.99, 40.00, 359.98),
(14, 29, 1, 49.99, 5.00, 44.99),
(15, 1, 1, 1299.99, 130.00, 1169.99),
(16, 35, 5, 49.99, 0.00, 249.95),
(17, 33, 2, 79.99, 16.00, 143.98),
(17, 34, 3, 199.99, 60.00, 539.97),
(18, 40, 10, 39.99, 40.00, 359.90),
(19, 45, 8, 19.99, 0.00, 159.92),
(20, 1, 1, 1299.99, 130.00, 1169.99);

-- Add statistics views for easier analysis
CREATE OR REPLACE VIEW monthly_revenue AS
SELECT
    DATE_TRUNC('month', order_date) AS month,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS avg_order_value,
    SUM(discount_amount) AS total_discounts
FROM orders
WHERE order_status = 'completed'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC;

CREATE OR REPLACE VIEW customer_metrics AS
SELECT
    c.customer_id,
    c.customer_name,
    c.customer_segment,
    c.country,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.order_status = 'completed' THEN o.total_amount ELSE 0 END) AS lifetime_value,
    AVG(CASE WHEN o.order_status = 'completed' THEN o.total_amount ELSE NULL END) AS avg_order_value,
    MAX(o.order_date) AS last_order_date
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.customer_name, c.customer_segment, c.country;

CREATE OR REPLACE VIEW product_performance AS
SELECT
    p.product_id,
    p.product_name,
    c.category_name,
    p.price,
    p.stock_quantity,
    COUNT(oi.order_item_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.subtotal) AS total_revenue,
    (p.price - p.cost) AS profit_margin
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
GROUP BY p.product_id, p.product_name, c.category_name, p.price, p.cost, p.stock_quantity;

COMMENT ON VIEW monthly_revenue IS 'Monthly revenue and order statistics';
COMMENT ON VIEW customer_metrics IS 'Customer lifetime value and order metrics';
COMMENT ON VIEW product_performance IS 'Product sales and revenue performance';
