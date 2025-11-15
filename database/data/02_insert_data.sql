-- E-Commerce Analytics Database - COMPREHENSIVE TEST DATA
-- Extensive dataset with 1000+ records for complex analytical queries
-- Includes data for all 23 tables with realistic relationships

-- =====================================================
-- DEPARTMENTS & EMPLOYEES
-- =====================================================

-- Insert Departments
INSERT INTO departments (department_name, description, budget) VALUES
('Sales', 'Sales and customer acquisition', 500000.00),
('Marketing', 'Marketing and promotions', 300000.00),
('Customer Service', 'Customer support and relations', 250000.00),
('Operations', 'Warehouse and logistics', 400000.00),
('IT', 'Information technology and systems', 350000.00),
('Finance', 'Financial planning and accounting', 200000.00),
('HR', 'Human resources', 180000.00);

-- Insert Employees (50 employees)
INSERT INTO employees (employee_name, email, phone, department_id, position, salary, hire_date, birth_date, manager_id, performance_rating, commission_rate) VALUES
-- Sales Department
('James Anderson', 'j.anderson@company.com', '+1-555-1001', 1, 'Sales Director', 95000.00, '2020-01-15', '1985-03-20', NULL, 4.5, 0.0500),
('Sarah Mitchell', 's.mitchell@company.com', '+1-555-1002', 1, 'Senior Sales Rep', 75000.00, '2020-06-01', '1988-07-12', 1, 4.3, 0.0350),
('Michael Chen', 'm.chen@company.com', '+1-555-1003', 1, 'Sales Representative', 65000.00, '2021-03-10', '1990-11-25', 1, 4.2, 0.0300),
('Emma Thompson', 'e.thompson@company.com', '+1-555-1004', 1, 'Sales Representative', 62000.00, '2021-08-15', '1992-05-08', 1, 4.4, 0.0300),
('David Rodriguez', 'd.rodriguez@company.com', '+1-555-1005', 1, 'Sales Representative', 68000.00, '2020-11-20', '1987-09-14', 1, 4.1, 0.0300),
('Lisa Wong', 'l.wong@company.com', '+1-555-1006', 1, 'Junior Sales Rep', 55000.00, '2022-02-01', '1994-12-30', 2, 3.9, 0.0250),
('Robert Johnson', 'r.johnson@company.com', '+1-555-1007', 1, 'Junior Sales Rep', 53000.00, '2022-05-15', '1995-04-18', 2, 3.8, 0.0250),

-- Marketing Department
('Jennifer Davis', 'j.davis@company.com', '+1-555-2001', 2, 'Marketing Director', 92000.00, '2019-09-01', '1984-06-22', NULL, 4.6, NULL),
('Kevin Brown', 'k.brown@company.com', '+1-555-2002', 2, 'Marketing Manager', 78000.00, '2020-03-15', '1986-10-05', 8, 4.4, NULL),
('Amanda Lee', 'a.lee@company.com', '+1-555-2003', 2, 'Content Specialist', 62000.00, '2021-01-20', '1991-08-17', 9, 4.2, NULL),
('Chris Martinez', 'c.martinez@company.com', '+1-555-2004', 2, 'Social Media Manager', 65000.00, '2021-06-10', '1993-02-28', 9, 4.3, NULL),

-- Customer Service Department
('Patricia Wilson', 'p.wilson@company.com', '+1-555-3001', 3, 'CS Director', 85000.00, '2019-12-01', '1983-11-15', NULL, 4.5, NULL),
('Thomas Garcia', 't.garcia@company.com', '+1-555-3002', 3, 'CS Manager', 70000.00, '2020-07-01', '1987-04-09', 12, 4.3, NULL),
('Maria Rodriguez', 'm.rodriguez@company.com', '+1-555-3003', 3, 'CS Representative', 52000.00, '2021-02-15', '1992-09-23', 13, 4.2, NULL),
('John Smith', 'j.smith@company.com', '+1-555-3004', 3, 'CS Representative', 51000.00, '2021-04-20', '1993-07-11', 13, 4.1, NULL),
('Emily Johnson', 'e.johnson@company.com', '+1-555-3005', 3, 'CS Representative', 53000.00, '2020-10-05', '1990-01-30', 13, 4.4, NULL),
('Daniel Kim', 'd.kim@company.com', '+1-555-3006', 3, 'CS Representative', 52000.00, '2022-01-10', '1994-06-14', 13, 4.0, NULL),

-- Operations Department
('Richard Taylor', 'r.taylor@company.com', '+1-555-4001', 4, 'Operations Director', 98000.00, '2018-05-01', '1982-08-25', NULL, 4.7, NULL),
('Susan Anderson', 's.anderson@company.com', '+1-555-4002', 4, 'Warehouse Manager', 72000.00, '2019-08-15', '1985-12-03', 18, 4.5, NULL),
('Mark Thompson', 'm.thompson@company.com', '+1-555-4003', 4, 'Warehouse Manager', 71000.00, '2019-11-20', '1986-05-19', 18, 4.4, NULL),
('Jessica White', 'j.white@company.com', '+1-555-4004', 4, 'Warehouse Manager', 70000.00, '2020-02-10', '1988-03-07', 18, 4.3, NULL),
('Brian Harris', 'b.harris@company.com', '+1-555-4005', 4, 'Logistics Coordinator', 58000.00, '2020-09-01', '1989-11-12', 18, 4.2, NULL),
('Michelle Clark', 'm.clark@company.com', '+1-555-4006', 4, 'Inventory Specialist', 54000.00, '2021-03-15', '1991-07-28', 19, 4.1, NULL),

-- IT Department
('Andrew Lewis', 'a.lewis@company.com', '+1-555-5001', 5, 'IT Director', 105000.00, '2018-01-10', '1981-04-16', NULL, 4.8, NULL),
('Rachel Walker', 'r.walker@company.com', '+1-555-5002', 5, 'Senior Developer', 88000.00, '2019-03-20', '1986-09-22', 24, 4.6, NULL),
('Steven Hall', 's.hall@company.com', '+1-555-5003', 5, 'Database Admin', 82000.00, '2019-07-15', '1987-12-05', 24, 4.5, NULL),
('Angela Allen', 'a.allen@company.com', '+1-555-5004', 5, 'Systems Analyst', 76000.00, '2020-04-01', '1989-06-18', 24, 4.4, NULL),

-- Finance Department
('William Young', 'w.young@company.com', '+1-555-6001', 6, 'Finance Director', 110000.00, '2017-09-01', '1980-02-28', NULL, 4.9, NULL),
('Karen King', 'k.king@company.com', '+1-555-6002', 6, 'Senior Accountant', 75000.00, '2019-01-15', '1985-10-14', 28, 4.5, NULL),
('George Wright', 'g.wright@company.com', '+1-555-6003', 6, 'Financial Analyst', 68000.00, '2020-06-10', '1988-08-21', 28, 4.3, NULL),

-- HR Department
('Barbara Scott', 'b.scott@company.com', '+1-555-7001', 7, 'HR Director', 95000.00, '2018-03-01', '1983-05-09', NULL, 4.6, NULL),
('Charles Green', 'c.green@company.com', '+1-555-7002', 7, 'HR Manager', 72000.00, '2019-10-15', '1986-11-27', 31, 4.4, NULL),
('Nancy Adams', 'n.adams@company.com', '+1-555-7003', 7, 'HR Specialist', 58000.00, '2020-12-01', '1990-03-15', 32, 4.2, NULL);

-- Update department managers
UPDATE departments SET manager_id = 1 WHERE department_id = 1;
UPDATE departments SET manager_id = 8 WHERE department_id = 2;
UPDATE departments SET manager_id = 12 WHERE department_id = 3;
UPDATE departments SET manager_id = 18 WHERE department_id = 4;
UPDATE departments SET manager_id = 24 WHERE department_id = 5;
UPDATE departments SET manager_id = 28 WHERE department_id = 6;
UPDATE departments SET manager_id = 31 WHERE department_id = 7;

-- =====================================================
-- WAREHOUSES
-- =====================================================

INSERT INTO warehouses (warehouse_name, country, region, city, address, capacity, manager_id, operating_cost) VALUES
('Los Angeles Distribution Center', 'USA', 'West', 'Los Angeles', '1234 Commerce Blvd, Los Angeles, CA 90001', 100000, 19, 45000.00),
('New York Fulfillment Center', 'USA', 'East', 'New York', '5678 Industrial Ave, Brooklyn, NY 11201', 85000, 20, 52000.00),
('Chicago Logistics Hub', 'USA', 'Central', 'Chicago', '910 Warehouse Dr, Chicago, IL 60601', 95000, 21, 42000.00),
('London Distribution Center', 'UK', 'South', 'London', '42 Commerce Park, London E14 5AB', 75000, 19, 38000.00),
('Toronto Fulfillment Center', 'Canada', 'Ontario', 'Toronto', '88 Distribution Way, Toronto, ON M5H 2N2', 70000, 20, 35000.00);

-- =====================================================
-- CATEGORIES (Hierarchical)
-- =====================================================

-- Top level categories
INSERT INTO categories (category_name, parent_category_id, description, display_order) VALUES
('Electronics', NULL, 'Electronic devices and accessories', 1),
('Clothing & Fashion', NULL, 'Apparel and fashion items', 2),
('Home & Garden', NULL, 'Home improvement and gardening', 3),
('Books & Media', NULL, 'Books, music, and educational materials', 4),
('Sports & Outdoors', NULL, 'Sports equipment and outdoor gear', 5),
('Toys & Games', NULL, 'Toys, games, and entertainment', 6),
('Health & Beauty', NULL, 'Health, wellness, and beauty products', 7),
('Food & Beverages', NULL, 'Groceries and beverages', 8),
('Office Supplies', NULL, 'Office and school supplies', 9),
('Pet Supplies', NULL, 'Pet food and accessories', 10);

-- Electronics subcategories
INSERT INTO categories (category_name, parent_category_id, description, display_order) VALUES
('Computers', 1, 'Laptops, desktops, and tablets', 1),
('Computer Accessories', 1, 'Keyboards, mice, monitors', 2),
('Audio', 1, 'Headphones, speakers, and audio equipment', 3),
('Mobile Devices', 1, 'Smartphones and accessories', 4),
('Cameras', 1, 'Digital cameras and photography equipment', 5);

-- Clothing subcategories
INSERT INTO categories (category_name, parent_category_id, description, display_order) VALUES
('Mens Clothing', 2, 'Men''s apparel', 1),
('Womens Clothing', 2, 'Women''s apparel', 2),
('Kids Clothing', 2, 'Children''s apparel', 3),
('Shoes', 2, 'Footwear for all', 4),
('Accessories', 2, 'Fashion accessories', 5);

-- Home & Garden subcategories
INSERT INTO categories (category_name, parent_category_id, description, display_order) VALUES
('Kitchen', 3, 'Kitchen appliances and tools', 1),
('Furniture', 3, 'Home furniture', 2),
('Garden Tools', 3, 'Gardening equipment', 3),
('Lighting', 3, 'Home lighting solutions', 4);

-- =====================================================
-- PRODUCTS (200+ products)
-- =====================================================

-- Generate SKUs and detailed product information
INSERT INTO products (product_name, sku, category_id, brand, price, cost, msrp, weight_kg, length_cm, width_cm, height_cm, manufacturer, warranty_months, is_featured, discount_percentage) VALUES
-- Computers (category 11)
('MacBook Pro 16"', 'COMP-MBP-16-001', 11, 'Apple', 2499.99, 1800.00, 2799.99, 2.0, 35.79, 24.59, 1.68, 'Apple Inc.', 12, TRUE, 0),
('Dell XPS 15', 'COMP-DXP-15-002', 11, 'Dell', 1899.99, 1350.00, 2199.99, 1.8, 34.4, 23.0, 1.8, 'Dell Technologies', 12, TRUE, 5.00),
('HP Pavilion 14', 'COMP-HPP-14-003', 11, 'HP', 799.99, 550.00, 999.99, 1.5, 32.5, 22.5, 1.79, 'HP Inc.', 12, FALSE, 10.00),
('Lenovo ThinkPad X1', 'COMP-LTP-X1-004', 11, 'Lenovo', 1599.99, 1100.00, 1899.99, 1.4, 31.8, 21.7, 1.49, 'Lenovo Group', 12, TRUE, 0),
('ASUS VivoBook', 'COMP-AVB-15-005', 11, 'ASUS', 699.99, 480.00, 849.99, 1.7, 36.0, 23.5, 1.99, 'ASUSTeK', 12, FALSE, 15.00),
('Microsoft Surface Laptop', 'COMP-MSL-13-006', 11, 'Microsoft', 1299.99, 900.00, 1499.99, 1.3, 30.8, 22.3, 1.45, 'Microsoft Corp', 12, TRUE, 0),
('Acer Aspire 5', 'COMP-ACA-15-007', 11, 'Acer', 549.99, 380.00, 699.99, 1.8, 36.3, 25.0, 1.79, 'Acer Inc.', 12, FALSE, 20.00),
('iPad Pro 12.9"', 'COMP-IPP-12-008', 11, 'Apple', 1099.99, 750.00, 1299.99, 0.68, 28.0, 21.5, 0.64, 'Apple Inc.', 12, TRUE, 0),

-- Computer Accessories (category 12)
('Logitech MX Master 3', 'ACC-LMM-3-009', 12, 'Logitech', 99.99, 55.00, 129.99, 0.14, 12.5, 8.4, 5.1, 'Logitech', 24, TRUE, 0),
('Apple Magic Keyboard', 'ACC-AMK-001-010', 12, 'Apple', 99.00, 50.00, 119.00, 0.23, 27.9, 11.5, 1.1, 'Apple Inc.', 12, FALSE, 0),
('Dell UltraSharp 27"', 'ACC-DUS-27-011', 12, 'Dell', 449.99, 280.00, 549.99, 5.4, 61.1, 18.6, 37.5, 'Dell Technologies', 36, TRUE, 10.00),
('Samsung 32" 4K Monitor', 'ACC-S32-4K-012', 12, 'Samsung', 399.99, 250.00, 499.99, 7.2, 71.4, 21.4, 42.6, 'Samsung Electronics', 24, TRUE, 5.00),
('Mechanical Gaming Keyboard RGB', 'ACC-MGK-RGB-013', 12, 'Corsair', 149.99, 85.00, 179.99, 1.2, 44.0, 16.6, 3.9, 'Corsair Gaming', 24, FALSE, 0),
('USB-C Docking Station', 'ACC-UCD-ST-014', 12, 'CalDigit', 279.99, 180.00, 329.99, 0.85, 15.7, 8.9, 2.9, 'CalDigit', 24, FALSE, 0),
('Wireless Webcam 1080p', 'ACC-WWC-HD-015', 12, 'Logitech', 89.99, 48.00, 109.99, 0.16, 9.5, 9.0, 7.1, 'Logitech', 24, FALSE, 10.00),
('External SSD 2TB', 'ACC-SSD-2T-016', 12, 'Samsung', 279.99, 170.00, 339.99, 0.05, 10.5, 5.7, 0.87, 'Samsung Electronics', 36, TRUE, 0),

-- Audio (category 13)
('Sony WH-1000XM5', 'AUD-SWH-XM5-017', 13, 'Sony', 399.99, 240.00, 449.99, 0.25, 21.4, 18.9, 8.0, 'Sony Corporation', 12, TRUE, 0),
('Bose QuietComfort 45', 'AUD-BQC-45-018', 13, 'Bose', 329.99, 200.00, 379.99, 0.24, 19.5, 15.2, 7.6, 'Bose Corporation', 12, TRUE, 5.00),
('AirPods Pro 2nd Gen', 'AUD-APP-2G-019', 13, 'Apple', 249.99, 145.00, 279.99, 0.05, 6.0, 4.5, 2.1, 'Apple Inc.', 12, TRUE, 0),
('JBL Flip 6 Speaker', 'AUD-JFL-6-020', 13, 'JBL', 129.99, 72.00, 149.99, 0.55, 17.8, 6.9, 7.2, 'Harman International', 12, FALSE, 10.00),
('Audio-Technica ATH-M50x', 'AUD-ATM-50X-021', 13, 'Audio-Technica', 149.99, 85.00, 179.99, 0.28, 22.0, 19.0, 9.5, 'Audio-Technica', 24, FALSE, 0),

-- Mobile Devices (category 14)
('iPhone 15 Pro', 'MOB-IP15-PRO-022', 14, 'Apple', 999.99, 650.00, 1199.99, 0.19, 14.7, 7.1, 0.83, 'Apple Inc.', 12, TRUE, 0),
('Samsung Galaxy S24', 'MOB-SGS-24-023', 14, 'Samsung', 899.99, 580.00, 1099.99, 0.17, 14.6, 7.0, 0.76, 'Samsung Electronics', 12, TRUE, 0),
('Google Pixel 8', 'MOB-GP8-001-024', 14, 'Google', 699.99, 450.00, 799.99, 0.19, 15.0, 7.1, 0.89, 'Google LLC', 12, FALSE, 5.00),
('Phone Case Universal', 'MOB-PCU-001-025', 14, 'OtterBox', 39.99, 18.00, 49.99, 0.08, 16.0, 8.0, 1.5, 'OtterBox', 12, FALSE, 15.00),

-- Cameras (category 15)
('Canon EOS R6', 'CAM-CER-6-026', 15, 'Canon', 2499.99, 1650.00, 2899.99, 0.68, 13.8, 9.8, 8.8, 'Canon Inc.', 12, TRUE, 0),
('Sony A7 IV', 'CAM-SA7-IV-027', 15, 'Sony', 2499.99, 1700.00, 2899.99, 0.66, 13.1, 9.6, 7.9, 'Sony Corporation', 12, TRUE, 0),
('GoPro HERO12', 'CAM-GPH-12-028', 15, 'GoPro', 399.99, 250.00, 499.99, 0.15, 7.1, 5.5, 3.4, 'GoPro Inc.', 12, FALSE, 10.00),

-- Men's Clothing (category 16)
('Levi''s 501 Jeans', 'CLO-L501-BLU-029', 16, 'Levi''s', 59.99, 28.00, 79.99, 0.6, 30.0, 25.0, 5.0, 'Levi Strauss', 0, FALSE, 0),
('Nike Dri-FIT T-Shirt', 'CLO-NDF-TSH-030', 16, 'Nike', 29.99, 12.00, 39.99, 0.2, 28.0, 20.0, 2.0, 'Nike Inc.', 0, FALSE, 20.00),
('Adidas Hoodie', 'CLO-ADH-GRY-031', 16, 'Adidas', 69.99, 32.00, 89.99, 0.5, 32.0, 28.0, 4.0, 'Adidas AG', 0, FALSE, 15.00),
('Ralph Lauren Polo', 'CLO-RLP-BLK-032', 16, 'Ralph Lauren', 89.99, 42.00, 119.99, 0.3, 29.0, 22.0, 3.0, 'Ralph Lauren Corp', 0, TRUE, 0),
('Columbia Winter Jacket', 'CLO-CWJ-BLK-033', 16, 'Columbia', 199.99, 110.00, 249.99, 1.2, 35.0, 30.0, 8.0, 'Columbia Sportswear', 12, TRUE, 5.00),

-- Women's Clothing (category 17)
('Lululemon Leggings', 'CLO-LLL-BLK-034', 17, 'Lululemon', 98.00, 45.00, 128.00, 0.3, 28.0, 20.0, 2.0, 'Lululemon', 0, TRUE, 0),
('Zara Floral Dress', 'CLO-ZFD-FLR-035', 17, 'Zara', 79.99, 35.00, 99.99, 0.4, 32.0, 25.0, 3.0, 'Zara', 0, FALSE, 10.00),
('H&M Blazer', 'CLO-HMB-BLK-036', 17, 'H&M', 89.99, 40.00, 119.99, 0.6, 30.0, 26.0, 4.0, 'H&M', 0, FALSE, 15.00),

-- Shoes (category 19)
('Nike Air Max 270', 'SHO-NAM-270-037', 19, 'Nike', 149.99, 75.00, 179.99, 0.9, 32.0, 20.0, 12.0, 'Nike Inc.', 6, TRUE, 0),
('Adidas Ultraboost', 'SHO-AUB-WHT-038', 19, 'Adidas', 179.99, 92.00, 219.99, 0.85, 31.0, 19.0, 11.5, 'Adidas AG', 6, TRUE, 5.00),
('Converse Chuck Taylor', 'SHO-CCT-BLK-039', 19, 'Converse', 59.99, 28.00, 74.99, 0.7, 30.0, 18.0, 10.0, 'Converse', 6, FALSE, 0),
('Timberland Boots', 'SHO-TBB-BRN-040', 19, 'Timberland', 189.99, 100.00, 229.99, 1.3, 32.0, 22.0, 13.0, 'Timberland LLC', 12, FALSE, 10.00),

-- Kitchen (category 21)
('Ninja Air Fryer', 'KIT-NAF-6QT-041', 21, 'Ninja', 119.99, 65.00, 149.99, 4.5, 33.0, 33.0, 33.0, 'SharkNinja', 12, TRUE, 15.00),
('KitchenAid Stand Mixer', 'KIT-KSM-5QT-042', 21, 'KitchenAid', 399.99, 240.00, 499.99, 10.0, 35.3, 22.1, 35.1, 'Whirlpool Corp', 12, TRUE, 0),
('Instant Pot Duo', 'KIT-IPD-6QT-043', 21, 'Instant Pot', 99.99, 52.00, 129.99, 5.5, 32.5, 31.5, 31.7, 'Instant Brands', 12, FALSE, 20.00),
('Breville Espresso Machine', 'KIT-BEM-001-044', 21, 'Breville', 699.99, 420.00, 849.99, 13.0, 32.0, 31.0, 40.0, 'Breville', 12, TRUE, 5.00),
('Cuisinart Food Processor', 'KIT-CFP-14C-045', 21, 'Cuisinart', 199.99, 115.00, 249.99, 8.2, 29.2, 21.6, 35.6, 'Cuisinart', 36, FALSE, 10.00),

-- Sports Equipment (category 5)
('Peloton Bike', 'SPT-PEL-BK-046', 5, 'Peloton', 1495.00, 980.00, 1895.00, 60.0, 122.0, 59.0, 135.0, 'Peloton Interactive', 12, TRUE, 0),
('NordicTrack Treadmill', 'SPT-NTT-1750-047', 5, 'NordicTrack', 1799.99, 1150.00, 2199.99, 105.0, 203.0, 97.0, 157.0, 'ICON Health', 24, TRUE, 5.00),
('Bowflex Dumbbells', 'SPT-BFD-552-048', 5, 'Bowflex', 549.99, 320.00, 699.99, 23.0, 40.6, 22.9, 22.9, 'Bowflex', 24, FALSE, 10.00),
('Yoga Mat Premium', 'SPT-YMP-6MM-049', 5, 'Manduka', 89.99, 42.00, 119.99, 3.2, 180.0, 66.0, 0.6, 'Manduka', 12, FALSE, 0),
('TRX Suspension Trainer', 'SPT-TRX-PRO-050', 5, 'TRX', 199.99, 110.00, 249.99, 1.8, 30.0, 25.0, 8.0, 'TRX', 12, FALSE, 15.00);

-- Add more products for variety (abbreviated for space)
INSERT INTO products (product_name, sku, category_id, brand, price, cost, msrp, weight_kg, is_featured, discount_percentage) VALUES
-- Books & Media (category 4)
('The Great Novel', 'BOK-TGN-001-051', 4, 'Penguin', 24.99, 12.00, 29.99, 0.5, FALSE, 0),
('Data Science Handbook', 'BOK-DSH-2024-052', 4, 'O''Reilly', 59.99, 30.00, 69.99, 0.8, TRUE, 10.00),
('Python Programming', 'BOK-PYP-ADV-053', 4, 'O''Reilly', 49.99, 24.00, 59.99, 0.7, FALSE, 0),
('Business Strategy', 'BOK-BST-MBA-054', 4, 'Harvard', 44.99, 22.00, 54.99, 0.6, FALSE, 5.00),
('Cookbook Mediterranean', 'BOK-CME-2024-055', 4, 'Taschen', 34.99, 17.00, 44.99, 1.2, FALSE, 0),

-- Toys & Games (category 6)
('LEGO Star Wars Set', 'TOY-LSW-001-056', 6, 'LEGO', 159.99, 85.00, 199.99, 1.5, TRUE, 10.00),
('Monopoly Classic', 'TOY-MON-CLA-057', 6, 'Hasbro', 29.99, 14.00, 39.99, 1.1, FALSE, 0),
('Nintendo Switch', 'TOY-NSW-OLE-058', 6, 'Nintendo', 349.99, 220.00, 399.99, 0.42, TRUE, 0),
('PlayStation 5', 'TOY-PS5-STD-059', 6, 'Sony', 499.99, 350.00, 549.99, 4.5, TRUE, 0),
('Xbox Series X', 'TOY-XSX-001-060', 6, 'Microsoft', 499.99, 345.00, 549.99, 4.45, TRUE, 0),

-- Health & Beauty (category 7)
('Dyson Hair Dryer', 'HEA-DHD-SUP-061', 7, 'Dyson', 429.99, 270.00, 499.99, 0.66, TRUE, 5.00),
('Oral-B Electric Toothbrush', 'HEA-OBE-IO9-062', 7, 'Oral-B', 199.99, 105.00, 249.99, 0.3, FALSE, 15.00),
('Vitamin D3 5000IU', 'HEA-VD3-5K-063', 7, 'Nature Made', 19.99, 8.00, 24.99, 0.1, FALSE, 0),
('Protein Powder 5lb', 'HEA-PPW-5LB-064', 7, 'Optimum', 59.99, 32.00, 74.99, 2.3, FALSE, 10.00),
('Face Serum Vitamin C', 'HEA-FSV-C30-065', 7, 'CeraVe', 39.99, 18.00, 49.99, 0.12, FALSE, 0),

-- Food & Beverages (category 8)
('Organic Coffee Beans 2lb', 'FOO-OCB-2LB-066', 8, 'Lavazza', 24.99, 12.00, 29.99, 0.91, FALSE, 0),
('Green Tea Matcha', 'FOO-GTM-100-067', 8, 'Ippodo', 34.99, 16.00, 44.99, 0.1, TRUE, 5.00),
('Olive Oil Extra Virgin 1L', 'FOO-OEV-1L-068', 8, 'Colavita', 29.99, 14.00, 39.99, 0.92, FALSE, 0),
('Almonds Raw 2lb', 'FOO-ALR-2LB-069', 8, 'Blue Diamond', 19.99, 9.00, 24.99, 0.91, FALSE, 10.00),
('Energy Bars Variety 20pk', 'FOO-EBV-20P-070', 8, 'CLIF', 24.99, 12.00, 29.99, 1.2, FALSE, 0),

-- Office Supplies (category 9)
('Stapler Heavy Duty', 'OFF-SHD-001-071', 9, 'Swingline', 29.99, 14.00, 39.99, 0.5, FALSE, 0),
('Paper Ream 5000 Sheets', 'OFF-PR5-WHT-072', 9, 'HP', 49.99, 22.00, 64.99, 12.0, FALSE, 15.00),
('Pen Set Ballpoint 50pk', 'OFF-PSB-50P-073', 9, 'BIC', 14.99, 6.00, 19.99, 0.6, FALSE, 0),
('Notebook Pack 10ct', 'OFF-NBP-10C-074', 9, 'Moleskine', 39.99, 18.00, 49.99, 1.5, FALSE, 10.00),

-- Pet Supplies (category 10)
('Dog Food Premium 30lb', 'PET-DFP-30L-075', 10, 'Blue Buffalo', 69.99, 38.00, 89.99, 13.6, FALSE, 10.00),
('Cat Litter 40lb', 'PET-CLT-40L-076', 10, 'Tidy Cats', 34.99, 16.00, 44.99, 18.1, FALSE, 0),
('Dog Bed Large', 'PET-DBL-001-077', 10, 'Furhaven', 89.99, 45.00, 119.99, 3.2, FALSE, 15.00),
('Cat Tree Tower', 'PET-CTT-6FT-078', 10, 'Frisco', 119.99, 62.00, 159.99, 15.0, TRUE, 10.00);

-- Add more products to reach 200+ total
INSERT INTO products (product_name, sku, category_id, brand, price, cost, weight_kg) VALUES
('Wireless Router AC1750', 'TECH-WRT-AC17-079', 12, 'TP-Link', 79.99, 42.00, 0.4),
('Smart Watch Series 9', 'TECH-SWS-9-080', 14, 'Apple', 399.99, 250.00, 0.05),
('Fitness Tracker', 'TECH-FTR-001-081', 14, 'Fitbit', 149.99, 82.00, 0.03),
('Portable Charger 20000mAh', 'TECH-PCH-20K-082', 12, 'Anker', 49.99, 24.00, 0.35),
('Hiking Backpack 50L', 'SPT-HBP-50L-083', 5, 'Osprey', 189.99, 105.00, 1.8),
('Camping Tent 4-Person', 'SPT-CT4-001-084', 5, 'Coleman', 199.99, 115.00, 8.5),
('Sleeping Bag 20F', 'SPT-SLB-20F-085', 5, 'North Face', 149.99, 85.00, 1.6),
('Water Bottle 32oz Steel', 'SPT-WBS-32-086', 5, 'Hydro Flask', 44.99, 22.00, 0.35),
('Bicycle Mountain 29"', 'SPT-BMT-29-087', 5, 'Trek', 899.99, 520.00, 14.0),
('Helmet Cycling', 'SPT-HCY-001-088', 5, 'Giro', 79.99, 42.00, 0.3),
('Running Shoes Trail', 'SHO-RST-001-089', 19, 'Salomon', 139.99, 75.00, 0.6),
('Basketball Official', 'SPT-BBO-NBA-090', 5, 'Spalding', 29.99, 14.00, 0.62),
('Tennis Racket Pro', 'SPT-TRP-001-091', 5, 'Wilson', 189.99, 105.00, 0.34),
('Golf Club Set', 'SPT-GCS-14P-092', 5, 'Callaway', 799.99, 450.00, 12.0),
('Desk Lamp LED', 'OFF-DLL-001-093', 9, 'TaoTronics', 39.99, 20.00, 0.8),
('Office Chair Ergonomic', 'OFF-OCE-001-094', 9, 'Herman Miller', 899.99, 520.00, 22.0),
('Standing Desk Electric', 'OFF-SDE-60-095', 9, 'FlexiSpot', 449.99, 260.00, 35.0),
('Monitor Arm Dual', 'OFF-MAD-002-096', 9, 'VIVO', 89.99, 45.00, 4.5),
('Coffee Maker Programmable', 'KIT-CMP-12C-097', 21, 'Mr. Coffee', 49.99, 24.00, 2.8),
('Blender High Speed', 'KIT-BHS-001-098', 21, 'Vitamix', 449.99, 270.00, 5.0),
('Toaster 4-Slice', 'KIT-T4S-001-099', 21, 'Cuisinart', 79.99, 42.00, 3.2),
('Vacuum Cordless', 'HOM-VCL-V11-100', 3, 'Dyson', 599.99, 360.00, 2.6);

-- Continue adding products to reach 200+ (abbreviated for brevity)
-- Adding 100 more simple products to reach target
DO $$
DECLARE
    i INTEGER;
    cat_id INTEGER;
    price NUMERIC;
BEGIN
    FOR i IN 101..200 LOOP
        cat_id := (i % 10) + 1; -- Rotate through categories
        price := 20.00 + (i * 2.5); -- Variable pricing
        INSERT INTO products (product_name, sku, category_id, brand, price, cost, weight_kg)
        VALUES (
            'Product Item ' || i,
            'GEN-PROD-' || LPAD(i::TEXT, 3, '0'),
            cat_id,
            CASE (i % 5)
                WHEN 0 THEN 'GenericBrand A'
                WHEN 1 THEN 'GenericBrand B'
                WHEN 2 THEN 'GenericBrand C'
                WHEN 3 THEN 'GenericBrand D'
                ELSE 'GenericBrand E'
            END,
            price,
            price * 0.55,
            0.5 + (i % 10) * 0.3
        );
    END LOOP;
END $$;

-- =====================================================
-- SUPPLIERS
-- =====================================================

INSERT INTO suppliers (supplier_name, contact_name, email, phone, country, city, rating, payment_terms) VALUES
('TechSupply Global', 'John Chen', 'j.chen@techsupply.com', '+1-800-555-0101', 'USA', 'San Francisco', 4.7, 'Net 30'),
('Electronics Wholesale Inc', 'Sarah Kim', 's.kim@ewholesale.com', '+1-800-555-0102', 'USA', 'Los Angeles', 4.5, 'Net 45'),
('Fashion Direct Ltd', 'Marie Dubois', 'm.dubois@fashiondirect.co.uk', '+44-800-123-4567', 'UK', 'London', 4.3, 'Net 30'),
('Sports Gear Distributors', 'Carlos Rodriguez', 'c.rodriguez@sportsgear.com', '+1-800-555-0103', 'USA', 'Chicago', 4.6, 'Net 30'),
('Home Essentials Supply', 'Anna Mueller', 'a.mueller@homeessentials.de', '+49-800-987-6543', 'Germany', 'Berlin', 4.4, 'Net 60'),
('Asian Electronics Hub', 'Li Wei', 'l.wei@asianhub.cn', '+86-800-888-8888', 'China', 'Shenzhen', 4.2, 'Net 45'),
('Premium Appliances Co', 'James Wilson', 'j.wilson@premiumappliances.com', '+1-800-555-0104', 'USA', 'New York', 4.8, 'Net 30'),
('Global Fashion Exports', 'Sofia Rossi', 's.rossi@globalfashion.it', '+39-800-555-7777', 'Italy', 'Milan', 4.5, 'Net 45'),
('Outdoor Adventure Supply', 'Erik Johansson', 'e.johansson@outdooradv.se', '+46-800-123-456', 'Sweden', 'Stockholm', 4.7, 'Net 30'),
('Book Publishing Group', 'Emma Taylor', 'e.taylor@bookpub.com', '+1-800-555-0105', 'USA', 'Boston', 4.6, 'Net 60'),
('Pet Products International', 'Robert Brown', 'r.brown@petproducts.com', '+1-800-555-0106', 'USA', 'Dallas', 4.4, 'Net 30'),
('Office Solutions Corp', 'Linda Garcia', 'l.garcia@officesolutions.com', '+1-800-555-0107', 'USA', 'Atlanta', 4.5, 'Net 45'),
('Health & Wellness Imports', 'David Park', 'd.park@healthimports.com', '+1-800-555-0108', 'USA', 'Seattle', 4.6, 'Net 30'),
('Food & Beverage Distributors', 'Maria Santos', 'm.santos@fooddist.com', '+1-800-555-0109', 'USA', 'Miami', 4.3, 'Net 30'),
('Toy Kingdom Supply', 'Michael Chang', 'm.chang@toykingdom.com', '+852-800-999-9999', 'Hong Kong', 'Kowloon', 4.5, 'Net 45');

-- =====================================================
-- PRODUCT-SUPPLIER RELATIONSHIPS
-- =====================================================

-- Create relationships between products and suppliers
INSERT INTO product_suppliers (product_id, supplier_id, supply_price, min_order_quantity, lead_time_days, is_preferred) VALUES
-- Electronics from multiple suppliers
(1, 1, 1750.00, 5, 7, TRUE),
(2, 1, 1300.00, 5, 7, TRUE),
(3, 2, 520.00, 10, 10, TRUE),
(4, 1, 1050.00, 5, 7, FALSE),
(5, 6, 450.00, 20, 14, TRUE),
(6, 1, 850.00, 5, 7, TRUE),
(7, 6, 360.00, 30, 21, TRUE),
(8, 1, 700.00, 10, 7, TRUE),
-- Accessories
(9, 2, 50.00, 50, 5, TRUE),
(10, 1, 45.00, 50, 5, TRUE),
(11, 2, 260.00, 10, 7, TRUE),
(12, 6, 230.00, 10, 14, TRUE),
(13, 2, 80.00, 20, 7, TRUE),
(14, 1, 170.00, 15, 7, TRUE),
(15, 2, 45.00, 30, 7, TRUE),
(16, 6, 160.00, 20, 10, TRUE),
-- Audio
(17, 1, 230.00, 10, 5, TRUE),
(18, 2, 190.00, 10, 5, TRUE),
(19, 1, 140.00, 20, 5, TRUE),
(20, 2, 68.00, 30, 7, TRUE),
(21, 2, 80.00, 20, 7, TRUE),
-- Mobile
(22, 1, 620.00, 5, 3, TRUE),
(23, 6, 560.00, 5, 10, TRUE),
(24, 1, 430.00, 10, 5, TRUE),
-- Clothing
(29, 3, 26.00, 100, 14, TRUE),
(30, 3, 11.00, 200, 14, TRUE),
(31, 8, 30.00, 100, 21, TRUE),
(32, 3, 40.00, 50, 14, TRUE),
(33, 9, 105.00, 30, 14, TRUE),
(34, 8, 42.00, 80, 21, TRUE),
-- Sports
(46, 4, 950.00, 5, 30, TRUE),
(47, 4, 1120.00, 3, 30, TRUE),
(48, 4, 310.00, 10, 14, TRUE),
(49, 9, 40.00, 50, 14, TRUE),
(50, 4, 105.00, 25, 14, TRUE);

-- Add more supplier relationships
DO $$
DECLARE
    i INTEGER;
    supplier_id_var INTEGER;
BEGIN
    FOR i IN 51..100 LOOP
        supplier_id_var := ((i - 51) % 15) + 1;
        INSERT INTO product_suppliers (product_id, supplier_id, supply_price, min_order_quantity, lead_time_days, is_preferred)
        SELECT i, supplier_id_var, p.cost * 0.95, 10, 7, TRUE
        FROM products p WHERE p.product_id = i;
    END LOOP;
END $$;

-- =====================================================
-- INVENTORY (Products distributed across warehouses)
-- =====================================================

-- Distribute inventory across warehouses for first 100 products
DO $$
DECLARE
    prod_id INTEGER;
    wh_id INTEGER;
    qty INTEGER;
BEGIN
    FOR prod_id IN 1..100 LOOP
        FOR wh_id IN 1..5 LOOP
            -- Not all products in all warehouses
            IF (prod_id + wh_id) % 3 != 0 THEN
                qty := 20 + (prod_id * wh_id) % 200;
                INSERT INTO inventory (product_id, warehouse_id, quantity, reserved_quantity, last_restock_date, bin_location)
                VALUES (
                    prod_id,
                    wh_id,
                    qty,
                    (qty * 0.1)::INTEGER, -- 10% reserved
                    CURRENT_DATE - ((prod_id + wh_id) % 90 || ' days')::INTERVAL,
                    'A' || ((prod_id % 26) + 1) || '-' || ((wh_id * 10) + (prod_id % 10))
                );
            END IF;
        END LOOP;
    END LOOP;
END $$;

-- =====================================================
-- CUSTOMERS (150 customers)
-- =====================================================

INSERT INTO customers (customer_name, email, phone, date_of_birth, gender, country, region, city, postal_code, signup_date, customer_segment, loyalty_tier, preferred_payment_method, marketing_consent, referral_source) VALUES
-- Premium US Customers
('John Anderson', 'john.anderson@email.com', '+1-555-2001', '1985-03-15', 'Male', 'USA', 'West', 'Los Angeles', '90001', '2022-01-10', 'Premium', 'Platinum', 'credit_card', TRUE, 'organic'),
('Sarah Williams', 'sarah.williams@email.com', '+1-555-2002', '1987-07-22', 'Female', 'USA', 'East', 'New York', '10001', '2022-01-15', 'Premium', 'Gold', 'credit_card', TRUE, 'referral'),
('Michael Johnson', 'michael.johnson@email.com', '+1-555-2003', '1983-11-08', 'Male', 'USA', 'West', 'San Francisco', '94102', '2022-02-01', 'Premium', 'Platinum', 'paypal', TRUE, 'organic'),
('Emily Davis', 'emily.davis@email.com', '+1-555-2004', '1990-05-17', 'Female', 'USA', 'East', 'Boston', '02101', '2022-02-10', 'Premium', 'Gold', 'credit_card', TRUE, 'social_media'),
('David Brown', 'david.brown@email.com', '+1-555-2005', '1982-09-25', 'Male', 'USA', 'Central', 'Chicago', '60601', '2022-02-20', 'Premium', 'Platinum', 'credit_card', TRUE, 'organic'),
('Jennifer Garcia', 'jennifer.garcia@email.com', '+1-555-2006', '1988-12-30', 'Female', 'USA', 'West', 'Seattle', '98101', '2022-03-01', 'Premium', 'Gold', 'credit_card', TRUE, 'referral'),
('Robert Martinez', 'robert.martinez@email.com', '+1-555-2007', '1986-04-12', 'Male', 'USA', 'South', 'Miami', '33101', '2022-03-15', 'Premium', 'Silver', 'paypal', TRUE, 'social_media'),
('Lisa Rodriguez', 'lisa.rodriguez@email.com', '+1-555-2008', '1991-08-19', 'Female', 'USA', 'South', 'Houston', '77001', '2022-04-01', 'Premium', 'Gold', 'credit_card', TRUE, 'organic'),
('William Taylor', 'william.taylor@email.com', '+1-555-2009', '1984-02-28', 'Male', 'USA', 'East', 'Philadelphia', '19101', '2022-04-10', 'Premium', 'Platinum', 'credit_card', TRUE, 'referral'),
('Mary Thomas', 'mary.thomas@email.com', '+1-555-2010', '1989-06-14', 'Female', 'USA', 'West', 'Portland', '97201', '2022-05-01', 'Premium', 'Gold', 'credit_card', TRUE, 'organic'),

-- Standard US Customers
('James Wilson', 'james.wilson@email.com', '+1-555-3001', '1992-01-20', 'Male', 'USA', 'West', 'San Diego', '92101', '2022-06-01', 'Standard', 'Silver', 'credit_card', TRUE, 'social_media'),
('Patricia Moore', 'patricia.moore@email.com', '+1-555-3002', '1986-10-05', 'Female', 'USA', 'East', 'Washington', '20001', '2022-06-15', 'Standard', 'Bronze', 'paypal', FALSE, 'organic'),
('Christopher Lee', 'christopher.lee@email.com', '+1-555-3003', '1993-03-18', 'Male', 'USA', 'South', 'Dallas', '75201', '2022-07-01', 'Standard', 'Silver', 'credit_card', TRUE, 'referral'),
('Linda White', 'linda.white@email.com', '+1-555-3004', '1988-07-22', 'Female', 'USA', 'Central', 'Minneapolis', '55401', '2022-07-15', 'Standard', 'Bronze', 'credit_card', FALSE, 'social_media'),
('Daniel Harris', 'daniel.harris@email.com', '+1-555-3005', '1990-11-11', 'Male', 'USA', 'West', 'Phoenix', '85001', '2022-08-01', 'Standard', 'Silver', 'paypal', TRUE, 'organic'),
('Barbara Martin', 'barbara.martin@email.com', '+1-555-3006', '1985-05-30', 'Female', 'USA', 'East', 'Atlanta', '30301', '2022-08-15', 'Standard', 'Silver', 'credit_card', TRUE, 'referral'),
('Matthew Thompson', 'matthew.thompson@email.com', '+1-555-3007', '1991-09-08', 'Male', 'USA', 'West', 'Denver', '80201', '2022-09-01', 'Standard', 'Bronze', 'credit_card', FALSE, 'social_media'),
('Susan Jackson', 'susan.jackson@email.com', '+1-555-3008', '1987-12-15', 'Female', 'USA', 'South', 'Austin', '78701', '2022-09-15', 'Standard', 'Silver', 'paypal', TRUE, 'organic'),
('Joseph White', 'joseph.white@email.com', '+1-555-3009', '1989-04-25', 'Male', 'USA', 'East', 'Charlotte', '28201', '2022-10-01', 'Standard', 'Bronze', 'credit_card', FALSE, 'referral'),
('Nancy Lopez', 'nancy.lopez@email.com', '+1-555-3010', '1992-08-03', 'Female', 'USA', 'West', 'Las Vegas', '89101', '2022-10-15', 'Standard', 'Silver', 'credit_card', TRUE, 'social_media');

-- Basic US Customers
INSERT INTO customers (customer_name, email, phone, country, region, city, signup_date, customer_segment, loyalty_tier, preferred_payment_method, marketing_consent, referral_source)
SELECT
    'Customer ' || i,
    'customer' || i || '@email.com',
    '+1-555-' || (4000 + i),
    'USA',
    CASE (i % 4)
        WHEN 0 THEN 'East'
        WHEN 1 THEN 'West'
        WHEN 2 THEN 'Central'
        ELSE 'South'
    END,
    CASE (i % 10)
        WHEN 0 THEN 'New York'
        WHEN 1 THEN 'Los Angeles'
        WHEN 2 THEN 'Chicago'
        WHEN 3 THEN 'Houston'
        WHEN 4 THEN 'Phoenix'
        WHEN 5 THEN 'Philadelphia'
        WHEN 6 THEN 'San Antonio'
        WHEN 7 THEN 'San Diego'
        WHEN 8 THEN 'Dallas'
        ELSE 'San Jose'
    END,
    '2023-01-01'::DATE + (i || ' days')::INTERVAL,
    'Basic',
    CASE (i % 3)
        WHEN 0 THEN 'Bronze'
        WHEN 1 THEN 'Silver'
        ELSE 'Bronze'
    END,
    CASE (i % 3)
        WHEN 0 THEN 'credit_card'
        WHEN 1 THEN 'paypal'
        ELSE 'bank_transfer'
    END,
    (i % 2 = 0),
    CASE (i % 4)
        WHEN 0 THEN 'organic'
        WHEN 1 THEN 'social_media'
        WHEN 2 THEN 'referral'
        ELSE 'email'
    END
FROM generate_series(21, 100) AS i;

-- International customers
INSERT INTO customers (customer_name, email, phone, country, region, city, signup_date, customer_segment, loyalty_tier, preferred_payment_method, marketing_consent) VALUES
('Oliver Smith', 'oliver.smith@email.co.uk', '+44-20-7123-4501', 'UK', 'South', 'London', '2023-01-15', 'Premium', 'Gold', 'credit_card', TRUE),
('Emma Thompson', 'emma.thompson@email.co.uk', '+44-161-555-0101', 'UK', 'North', 'Manchester', '2023-02-01', 'Standard', 'Silver', 'paypal', TRUE),
('James Brown', 'james.brown@email.co.uk', '+44-121-555-0102', 'UK', 'Midlands', 'Birmingham', '2023-02-15', 'Basic', 'Bronze', 'credit_card', FALSE),
('Sophie Clark', 'sophie.clark@email.co.uk', '+44-131-555-0103', 'UK', 'Scotland', 'Edinburgh', '2023-03-01', 'Standard', 'Silver', 'credit_card', TRUE),
('Harry Davies', 'harry.davies@email.co.uk', '+44-117-555-0104', 'UK', 'South West', 'Bristol', '2023-03-15', 'Premium', 'Gold', 'credit_card', TRUE),
('Pierre Dubois', 'pierre.dubois@email.ca', '+1-514-555-0201', 'Canada', 'Quebec', 'Montreal', '2023-01-20', 'Standard', 'Silver', 'credit_card', TRUE),
('Anna Kowalski', 'anna.kowalski@email.ca', '+1-416-555-0202', 'Canada', 'Ontario', 'Toronto', '2023-02-05', 'Premium', 'Platinum', 'credit_card', TRUE),
('Ryan Chen', 'ryan.chen@email.ca', '+1-604-555-0203', 'Canada', 'BC', 'Vancouver', '2023-02-20', 'Standard', 'Silver', 'paypal', TRUE),
('Sophie Tremblay', 'sophie.tremblay@email.ca', '+1-403-555-0204', 'Canada', 'Alberta', 'Calgary', '2023-03-10', 'Basic', 'Bronze', 'credit_card', FALSE),
('Lucas Martin', 'lucas.martin@email.ca', '+1-613-555-0205', 'Canada', 'Ontario', 'Ottawa', '2023-04-01', 'Standard', 'Silver', 'credit_card', TRUE);

-- Add 40 more international customers
INSERT INTO customers (customer_name, email, country, region, city, signup_date, customer_segment, loyalty_tier, preferred_payment_method, marketing_consent)
SELECT
    'IntlCustomer ' || i,
    'intl' || i || '@email.com',
    CASE (i % 3)
        WHEN 0 THEN 'UK'
        WHEN 1 THEN 'Canada'
        ELSE 'Australia'
    END,
    'International',
    CASE (i % 5)
        WHEN 0 THEN 'London'
        WHEN 1 THEN 'Toronto'
        WHEN 2 THEN 'Sydney'
        WHEN 3 THEN 'Vancouver'
        ELSE 'Melbourne'
    END,
    '2023-05-01'::DATE + (i || ' days')::INTERVAL,
    CASE (i % 3)
        WHEN 0 THEN 'Premium'
        WHEN 1 THEN 'Standard'
        ELSE 'Basic'
    END,
    CASE (i % 4)
        WHEN 0 THEN 'Platinum'
        WHEN 1 THEN 'Gold'
        WHEN 2 THEN 'Silver'
        ELSE 'Bronze'
    END,
    'credit_card',
    (i % 2 = 0)
FROM generate_series(111, 150) AS i;

-- =====================================================
-- PROMOTIONS
-- =====================================================

INSERT INTO promotions (promotion_name, promotion_code, description, discount_type, discount_value, min_purchase_amount, start_date, end_date, usage_limit, created_by) VALUES
('New Year 2023', 'NEWYEAR2023', '15% off all orders', 'percentage', 15.00, 50.00, '2023-01-01', '2023-01-31', 1000, 8),
('Spring Sale', 'SPRING2023', '$25 off orders over $150', 'fixed_amount', 25.00, 150.00, '2023-03-01', '2023-03-31', 500, 8),
('Summer Savings', 'SUMMER2023', '20% off electronics', 'percentage', 20.00, 100.00, '2023-06-01', '2023-08-31', 750, 8),
('Back to School', 'SCHOOL2023', '$30 off $200+', 'fixed_amount', 30.00, 200.00, '2023-08-01', '2023-09-15', 400, 8),
('Black Friday', 'BFRIDAY2023', '30% off everything', 'percentage', 30.00, 75.00, '2023-11-24', '2023-11-26', 2000, 8),
('Cyber Monday', 'CYBERMON2023', '25% off tech products', 'percentage', 25.00, 100.00, '2023-11-27', '2023-11-27', 1500, 8),
('Holiday Season', 'HOLIDAY2023', '$50 off $300+', 'fixed_amount', 50.00, 300.00, '2023-12-01', '2023-12-31', 1000, 8),
('New Year 2024', 'NEWYEAR2024', '20% off sitewide', 'percentage', 20.00, 100.00, '2024-01-01', '2024-01-31', 1200, 8),
('Valentine Special', 'VALENTINE24', 'Free shipping on all orders', 'free_shipping', 0.00, 50.00, '2024-02-10', '2024-02-14', 800, 8),
('Spring Flash', 'SPRING24', '$40 off $250+', 'fixed_amount', 40.00, 250.00, '2024-03-15', '2024-03-31', 600, 8),
('Earth Day', 'EARTHDAY24', '15% off eco products', 'percentage', 15.00, 75.00, '2024-04-20', '2024-04-25', 300, 8),
('Mother''s Day', 'MOMSDAY24', '$20 off $150+', 'fixed_amount', 20.00, 150.00, '2024-05-08', '2024-05-12', 500, 8),
('Summer Kickoff', 'SUMMERKICK24', '18% off outdoor gear', 'percentage', 18.00, 100.00, '2024-05-25', '2024-06-10', 450, 8),
('Prime Day', 'PRIMEDAY24', '35% off selected items', 'percentage', 35.00, 50.00, '2024-07-15', '2024-07-16', 2500, 8),
('Labor Day', 'LABORDAY24', '$35 off $200+', 'fixed_amount', 35.00, 200.00, '2024-09-01', '2024-09-03', 700, 8);

-- =====================================================
-- ORDERS (800+ orders from 2023-2024)
-- =====================================================

-- Helper function to generate random order data
DO $$
DECLARE
    order_count INTEGER := 0;
    cust_id INTEGER;
    emp_id INTEGER;
    wh_id INTEGER;
    order_dt TIMESTAMP;
    total DECIMAL(10,2);
    promo_id INTEGER;
BEGIN
    -- Generate orders throughout 2023-2024
    FOR order_count IN 1..800 LOOP
        -- Random customer (weighted towards first 50 customers who order more)
        IF random() < 0.6 THEN
            cust_id := (random() * 49 + 1)::INTEGER;
        ELSE
            cust_id := (random() * 149 + 1)::INTEGER;
        END IF;

        -- Random sales employee (1-7 are sales)
        emp_id := (random() * 6 + 1)::INTEGER;

        -- Random warehouse
        wh_id := (random() * 4 + 1)::INTEGER;

        -- Order date spread across 2023-2024
        order_dt := '2023-01-01'::TIMESTAMP + (random() * 700 || ' days')::INTERVAL + (random() * 86400 || ' seconds')::INTERVAL;

        -- Random total amount
        total := (50 + random() * 2000)::DECIMAL(10,2);

        INSERT INTO orders (
            order_number,
            customer_id,
            employee_id,
            warehouse_id,
            order_date,
            order_status,
            total_amount,
            discount_amount,
            tax_amount,
            shipping_cost,
            payment_method,
            payment_status,
            shipping_country,
            shipping_region,
            expected_delivery_date,
            actual_delivery_date
        ) VALUES (
            'ORD-' || TO_CHAR(order_dt, 'YYYY') || '-' || LPAD(order_count::TEXT, 6, '0'),
            cust_id,
            emp_id,
            wh_id,
            order_dt,
            CASE (random() * 100)::INTEGER
                WHEN 0 THEN 'cancelled'
                WHEN 1 THEN 'refunded'
                WHEN 2,3,4 THEN 'pending'
                WHEN 5,6,7,8 THEN 'processing'
                WHEN 9,10,11,12,13 THEN 'shipped'
                ELSE 'delivered'
            END,
            total,
            (total * random() * 0.15)::DECIMAL(10,2), -- 0-15% discount
            (total * 0.08)::DECIMAL(10,2), -- 8% tax
            CASE (random() * 3)::INTEGER
                WHEN 0 THEN 10.00
                WHEN 1 THEN 15.00
                ELSE 20.00
            END,
            CASE (random() * 3)::INTEGER
                WHEN 0 THEN 'credit_card'
                WHEN 1 THEN 'paypal'
                ELSE 'bank_transfer'
            END,
            CASE (random() * 20)::INTEGER
                WHEN 0 THEN 'failed'
                WHEN 1 THEN 'pending'
                ELSE 'completed'
            END,
            CASE (cust_id % 3)
                WHEN 0 THEN 'USA'
                WHEN 1 THEN 'UK'
                ELSE 'Canada'
            END,
            'Region ' || ((cust_id % 5) + 1),
            order_dt + '5 days'::INTERVAL,
            CASE
                WHEN random() < 0.85 THEN order_dt + (4 + random() * 3)::INTEGER || ' days'
                ELSE NULL
            END
        );
    END LOOP;
END $$;

-- =====================================================
-- ORDER ITEMS (2-5 items per order)
-- =====================================================

DO $$
DECLARE
    ord_id INTEGER;
    num_items INTEGER;
    item_count INTEGER;
    prod_id INTEGER;
    qty INTEGER;
    unit_pr DECIMAL(10,2);
BEGIN
    FOR ord_id IN 1..800 LOOP
        num_items := (random() * 4 + 1)::INTEGER; -- 1-5 items per order

        FOR item_count IN 1..num_items LOOP
            prod_id := (random() * 99 + 1)::INTEGER; -- Random product from first 100
            qty := (random() * 4 + 1)::INTEGER; -- 1-5 quantity

            SELECT price INTO unit_pr FROM products WHERE product_id = prod_id;

            INSERT INTO order_items (
                order_id,
                product_id,
                quantity,
                unit_price,
                discount_amount,
                tax_amount,
                subtotal,
                cost_at_time
            )
            SELECT
                ord_id,
                prod_id,
                qty,
                unit_pr,
                (unit_pr * qty * random() * 0.1)::DECIMAL(10,2),
                (unit_pr * qty * 0.08)::DECIMAL(10,2),
                (unit_pr * qty)::DECIMAL(10,2),
                cost
            FROM products WHERE product_id = prod_id;
        END LOOP;
    END LOOP;
END $$;

-- =====================================================
-- ORDER PROMOTIONS (Apply promotions to ~20% of orders)
-- =====================================================

INSERT INTO order_promotions (order_id, promotion_id, discount_applied)
SELECT
    o.order_id,
    (random() * 14 + 1)::INTEGER,
    (o.total_amount * (0.05 + random() * 0.20))::DECIMAL(10,2)
FROM orders o
WHERE random() < 0.20
LIMIT 160;

-- =====================================================
-- PAYMENT TRANSACTIONS (One per order)
-- =====================================================

INSERT INTO payment_transactions (
    order_id,
    transaction_reference,
    payment_method,
    payment_provider,
    amount,
    status,
    transaction_date,
    processed_date,
    provider_fee
)
SELECT
    order_id,
    'TXN-' || order_number,
    payment_method,
    CASE payment_method
        WHEN 'credit_card' THEN 'Stripe'
        WHEN 'paypal' THEN 'PayPal'
        ELSE 'Bank Transfer'
    END,
    total_amount,
    payment_status,
    order_date,
    order_date + '2 hours'::INTERVAL,
    (total_amount * 0.029 + 0.30)::DECIMAL(10,2) -- Typical payment processing fee
FROM orders;

-- =====================================================
-- SHIPMENTS (For non-cancelled orders)
-- =====================================================

INSERT INTO shipments (
    order_id,
    warehouse_id,
    tracking_number,
    carrier,
    shipping_method,
    shipment_status,
    ship_date,
    estimated_delivery,
    actual_delivery,
    weight_kg,
    shipping_cost
)
SELECT
    o.order_id,
    o.warehouse_id,
    'TRACK-' || o.order_number,
    CASE (o.order_id % 4)
        WHEN 0 THEN 'FedEx'
        WHEN 1 THEN 'UPS'
        WHEN 2 THEN 'USPS'
        ELSE 'DHL'
    END,
    CASE (o.order_id % 3)
        WHEN 0 THEN 'standard'
        WHEN 1 THEN 'express'
        ELSE 'overnight'
    END,
    CASE o.order_status
        WHEN 'delivered' THEN 'delivered'
        WHEN 'shipped' THEN 'in_transit'
        WHEN 'processing' THEN 'packed'
        ELSE 'pending'
    END,
    o.order_date + '1 day'::INTERVAL,
    o.expected_delivery_date,
    o.actual_delivery_date,
    (2.0 + random() * 15)::DECIMAL(8,3),
    o.shipping_cost
FROM orders o
WHERE o.order_status NOT IN ('cancelled', 'refunded');

-- =====================================================
-- SHIPMENT TRACKING (3-5 events per shipment)
-- =====================================================

DO $$
DECLARE
    ship_rec RECORD;
    num_events INTEGER;
    event_num INTEGER;
    event_dt TIMESTAMP;
BEGIN
    FOR ship_rec IN SELECT shipment_id, ship_date, estimated_delivery FROM shipments LIMIT 200 LOOP
        num_events := (random() * 3 + 2)::INTEGER; -- 2-5 events

        FOR event_num IN 1..num_events LOOP
            event_dt := ship_rec.ship_date + ((event_num - 1) || ' days')::INTERVAL;

            INSERT INTO shipment_tracking (
                shipment_id,
                location,
                status,
                description,
                event_date
            ) VALUES (
                ship_rec.shipment_id,
                CASE event_num
                    WHEN 1 THEN 'Origin Facility'
                    WHEN 2 THEN 'In Transit'
                    WHEN 3 THEN 'Sorting Facility'
                    WHEN 4 THEN 'Out for Delivery'
                    ELSE 'Delivered'
                END,
                CASE event_num
                    WHEN 1 THEN 'Picked up'
                    WHEN 2 THEN 'In transit'
                    WHEN 3 THEN 'Arrived at facility'
                    WHEN 4 THEN 'Out for delivery'
                    ELSE 'Delivered'
                END,
                'Package ' || CASE event_num
                    WHEN 1 THEN 'picked up from warehouse'
                    WHEN 2 THEN 'in transit to destination'
                    WHEN 3 THEN 'arrived at sorting facility'
                    WHEN 4 THEN 'out for delivery'
                    ELSE 'delivered to customer'
                END,
                event_dt
            );
        END LOOP;
    END LOOP;
END $$;

-- =====================================================
-- REVIEWS (100+ reviews)
-- =====================================================

INSERT INTO reviews (product_id, customer_id, order_id, rating, title, review_text, is_verified_purchase, helpful_count, is_approved)
SELECT
    (random() * 99 + 1)::INTEGER,
    (random() * 49 + 1)::INTEGER,
    (random() * 799 + 1)::INTEGER,
    (random() * 4 + 1)::INTEGER + 1, -- 1-5 stars
    CASE (random() * 5)::INTEGER
        WHEN 0 THEN 'Great product!'
        WHEN 1 THEN 'Excellent quality'
        WHEN 2 THEN 'Good value'
        WHEN 3 THEN 'As expected'
        ELSE 'Satisfied with purchase'
    END,
    'This product ' || CASE (random() * 3)::INTEGER
        WHEN 0 THEN 'exceeded my expectations. Highly recommend!'
        WHEN 1 THEN 'was exactly what I needed. Good quality.'
        ELSE 'met my needs. Would buy again.'
    END,
    TRUE,
    (random() * 50)::INTEGER,
    TRUE
FROM generate_series(1, 150);

-- =====================================================
-- RETURNS (50 returns)
-- =====================================================

INSERT INTO returns (
    order_id,
    customer_id,
    return_number,
    return_date,
    reason,
    status,
    refund_amount,
    restocking_fee,
    approved_by,
    processed_by
)
SELECT
    o.order_id,
    o.customer_id,
    'RET-' || o.order_number,
    o.order_date + (10 + random() * 20)::INTEGER || ' days',
    CASE (random() * 5)::INTEGER
        WHEN 0 THEN 'Defective item'
        WHEN 1 THEN 'Wrong item received'
        WHEN 2 THEN 'No longer needed'
        WHEN 3 THEN 'Better price elsewhere'
        ELSE 'Did not meet expectations'
    END,
    CASE (random() * 4)::INTEGER
        WHEN 0 THEN 'refunded'
        WHEN 1 THEN 'received'
        WHEN 2 THEN 'approved'
        ELSE 'requested'
    END,
    (o.total_amount * (0.8 + random() * 0.2))::DECIMAL(10,2),
    CASE WHEN random() < 0.3 THEN 15.00 ELSE 0.00 END,
    12, -- CS Director
    13  -- CS Manager
FROM orders o
WHERE o.order_status = 'delivered'
    AND random() < 0.08
LIMIT 50;

-- =====================================================
-- RETURN ITEMS (Matching returns)
-- =====================================================

INSERT INTO return_items (
    return_id,
    order_item_id,
    product_id,
    quantity,
    reason,
    condition,
    refund_amount
)
SELECT
    r.return_id,
    oi.order_item_id,
    oi.product_id,
    LEAST(oi.quantity, (random() * oi.quantity + 1)::INTEGER),
    r.reason,
    CASE (random() * 4)::INTEGER
        WHEN 0 THEN 'new'
        WHEN 1 THEN 'opened'
        WHEN 2 THEN 'used'
        ELSE 'damaged'
    END,
    (oi.subtotal * 0.9)::DECIMAL(10,2)
FROM returns r
JOIN order_items oi ON r.order_id = oi.order_id
WHERE oi.order_item_id IN (
    SELECT order_item_id FROM order_items WHERE order_id = r.order_id ORDER BY RANDOM() LIMIT 1
);

-- =====================================================
-- CUSTOMER INTERACTIONS (100 interactions)
-- =====================================================

INSERT INTO customer_interactions (
    customer_id,
    employee_id,
    interaction_type,
    subject,
    description,
    status,
    priority,
    satisfaction_rating,
    interaction_date,
    resolved_date
)
SELECT
    (random() * 149 + 1)::INTEGER,
    (random() * 4 + 13)::INTEGER, -- CS employees
    CASE (random() * 4)::INTEGER
        WHEN 0 THEN 'call'
        WHEN 1 THEN 'email'
        WHEN 2 THEN 'chat'
        ELSE 'ticket'
    END,
    CASE (random() * 6)::INTEGER
        WHEN 0 THEN 'Order status inquiry'
        WHEN 1 THEN 'Product question'
        WHEN 2 THEN 'Return request'
        WHEN 3 THEN 'Shipping issue'
        WHEN 4 THEN 'Payment problem'
        ELSE 'General inquiry'
    END,
    'Customer contacted regarding ' || CASE (random() * 3)::INTEGER
        WHEN 0 THEN 'order delivery status and tracking information'
        WHEN 1 THEN 'product features and compatibility questions'
        ELSE 'assistance with account or billing'
    END,
    CASE (random() * 4)::INTEGER
        WHEN 0 THEN 'closed'
        WHEN 1 THEN 'resolved'
        WHEN 2 THEN 'in_progress'
        ELSE 'open'
    END,
    CASE (random() * 4)::INTEGER
        WHEN 0 THEN 'urgent'
        WHEN 1 THEN 'high'
        WHEN 2 THEN 'medium'
        ELSE 'low'
    END,
    CASE WHEN random() < 0.7 THEN (random() * 2 + 3)::INTEGER ELSE NULL END, -- 3-5 rating for resolved
    '2023-01-01'::TIMESTAMP + (random() * 700 || ' days')::INTERVAL,
    CASE WHEN random() < 0.7 THEN
        '2023-01-01'::TIMESTAMP + (random() * 700 || ' days')::INTERVAL + '2 days'::INTERVAL
    ELSE NULL END
FROM generate_series(1, 100);

-- =====================================================
-- LOYALTY TRANSACTIONS (For premium customers)
-- =====================================================

INSERT INTO loyalty_transactions (
    customer_id,
    points,
    transaction_type,
    order_id,
    description,
    balance_after,
    transaction_date
)
SELECT
    o.customer_id,
    (o.total_amount * 0.1)::INTEGER, -- 10% of order as points
    'earned',
    o.order_id,
    'Points earned from order ' || o.order_number,
    (o.total_amount * 0.1)::INTEGER,
    o.order_date
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE c.customer_segment = 'Premium'
    AND o.order_status IN ('delivered', 'shipped')
LIMIT 200;

-- =====================================================
-- WISHLIST ITEMS
-- =====================================================

INSERT INTO wishlist_items (customer_id, product_id, priority, notes)
SELECT
    (random() * 149 + 1)::INTEGER,
    (random() * 99 + 1)::INTEGER,
    (random() * 5)::INTEGER,
    CASE WHEN random() < 0.3 THEN 'Want to buy when on sale' ELSE NULL END
FROM generate_series(1, 150)
ON CONFLICT DO NOTHING;

-- =====================================================
-- CART ITEMS (Abandoned carts)
-- =====================================================

INSERT INTO cart_items (customer_id, product_id, quantity, is_active)
SELECT
    (random() * 149 + 1)::INTEGER,
    (random() * 99 + 1)::INTEGER,
    (random() * 4 + 1)::INTEGER,
    TRUE
FROM generate_series(1, 80)
ON CONFLICT DO NOTHING;

-- =====================================================
-- END OF DATA INSERTS
-- =====================================================

-- Update customer lifetime values based on actual orders
UPDATE customers c
SET total_lifetime_value = COALESCE(
    (SELECT SUM(total_amount)
     FROM orders o
     WHERE o.customer_id = c.customer_id
       AND o.order_status IN ('delivered', 'shipped', 'processing')),
    0
);

-- Update promotion usage counts
UPDATE promotions p
SET times_used = (
    SELECT COUNT(*)
    FROM order_promotions op
    WHERE op.promotion_id = p.promotion_id
);
