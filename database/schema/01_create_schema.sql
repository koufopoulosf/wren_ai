-- E-Commerce Analytics Database Schema - EXTENDED VERSION
-- Comprehensive schema with 15+ tables for complex analytical queries
-- Supports multi-table joins, window functions, aggregations, and advanced analytics

-- Drop all existing tables in correct order (respecting foreign keys)
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS wishlist_items CASCADE;
DROP TABLE IF EXISTS loyalty_transactions CASCADE;
DROP TABLE IF EXISTS customer_interactions CASCADE;
DROP TABLE IF EXISTS payment_transactions CASCADE;
DROP TABLE IF EXISTS return_items CASCADE;
DROP TABLE IF EXISTS returns CASCADE;
DROP TABLE IF EXISTS shipment_tracking CASCADE;
DROP TABLE IF EXISTS shipments CASCADE;
DROP TABLE IF EXISTS order_promotions CASCADE;
DROP TABLE IF EXISTS promotions CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;
DROP TABLE IF EXISTS product_suppliers CASCADE;
DROP TABLE IF EXISTS suppliers CASCADE;
DROP TABLE IF EXISTS warehouses CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS customers CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS categories CASCADE;
DROP TABLE IF EXISTS employees CASCADE;
DROP TABLE IF EXISTS departments CASCADE;

-- =====================================================
-- CORE ORGANIZATIONAL TABLES
-- =====================================================

-- Departments table
CREATE TABLE departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    description TEXT,
    budget DECIMAL(12, 2),
    manager_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees table
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    employee_name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    phone VARCHAR(50),
    department_id INTEGER REFERENCES departments(department_id),
    position VARCHAR(100),
    salary DECIMAL(10, 2),
    hire_date DATE NOT NULL,
    birth_date DATE,
    manager_id INTEGER REFERENCES employees(employee_id),
    is_active BOOLEAN DEFAULT TRUE,
    performance_rating DECIMAL(3, 2), -- 0.00 to 5.00
    commission_rate DECIMAL(5, 4), -- e.g., 0.0250 for 2.5%
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key for department manager
ALTER TABLE departments ADD CONSTRAINT fk_dept_manager
    FOREIGN KEY (manager_id) REFERENCES employees(employee_id);

-- Warehouses table
CREATE TABLE warehouses (
    warehouse_id SERIAL PRIMARY KEY,
    warehouse_name VARCHAR(200) NOT NULL,
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    capacity INTEGER,
    manager_id INTEGER REFERENCES employees(employee_id),
    is_active BOOLEAN DEFAULT TRUE,
    operating_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- PRODUCT & CATEGORY TABLES
-- =====================================================

-- Categories table (hierarchical)
CREATE TABLE categories (
    category_id SERIAL PRIMARY KEY,
    category_name VARCHAR(100) NOT NULL,
    parent_category_id INTEGER REFERENCES categories(category_id),
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products table (expanded)
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    sku VARCHAR(100) UNIQUE,
    category_id INTEGER REFERENCES categories(category_id),
    brand VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    msrp DECIMAL(10, 2), -- Manufacturer's Suggested Retail Price
    weight_kg DECIMAL(8, 3),
    length_cm DECIMAL(8, 2),
    width_cm DECIMAL(8, 2),
    height_cm DECIMAL(8, 2),
    manufacturer VARCHAR(200),
    warranty_months INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    discount_percentage DECIMAL(5, 2) DEFAULT 0,
    min_order_quantity INTEGER DEFAULT 1,
    max_order_quantity INTEGER DEFAULT 999,
    reorder_level INTEGER DEFAULT 10,
    lead_time_days INTEGER DEFAULT 7,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(200),
    email VARCHAR(200),
    phone VARCHAR(50),
    country VARCHAR(100),
    city VARCHAR(100),
    address TEXT,
    rating DECIMAL(3, 2), -- 0.00 to 5.00
    payment_terms VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Product-Supplier relationship (many-to-many)
CREATE TABLE product_suppliers (
    product_supplier_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    supply_price DECIMAL(10, 2),
    min_order_quantity INTEGER DEFAULT 1,
    lead_time_days INTEGER DEFAULT 7,
    is_preferred BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, supplier_id)
);

-- Inventory table (by warehouse)
CREATE TABLE inventory (
    inventory_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    warehouse_id INTEGER REFERENCES warehouses(warehouse_id),
    quantity INTEGER NOT NULL DEFAULT 0,
    reserved_quantity INTEGER DEFAULT 0, -- Reserved for pending orders
    available_quantity INTEGER GENERATED ALWAYS AS (quantity - reserved_quantity) STORED,
    last_restock_date DATE,
    last_count_date DATE,
    bin_location VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, warehouse_id)
);

-- =====================================================
-- CUSTOMER TABLES
-- =====================================================

-- Customers table (expanded)
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_name VARCHAR(200) NOT NULL,
    email VARCHAR(200) UNIQUE NOT NULL,
    phone VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20),
    country VARCHAR(100),
    region VARCHAR(100),
    city VARCHAR(100),
    postal_code VARCHAR(20),
    address TEXT,
    signup_date DATE NOT NULL,
    customer_segment VARCHAR(50), -- 'Premium', 'Standard', 'Basic'
    loyalty_tier VARCHAR(50), -- 'Platinum', 'Gold', 'Silver', 'Bronze'
    is_active BOOLEAN DEFAULT TRUE,
    total_lifetime_value DECIMAL(12, 2) DEFAULT 0,
    preferred_payment_method VARCHAR(50),
    marketing_consent BOOLEAN DEFAULT FALSE,
    referral_source VARCHAR(100),
    last_login_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Loyalty Points table
CREATE TABLE loyalty_transactions (
    transaction_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    points INTEGER NOT NULL,
    transaction_type VARCHAR(50), -- 'earned', 'redeemed', 'expired', 'adjusted'
    order_id INTEGER, -- References orders, but we'll add FK later
    description TEXT,
    balance_after INTEGER NOT NULL,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Interactions table (support, calls, emails)
CREATE TABLE customer_interactions (
    interaction_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    interaction_type VARCHAR(50), -- 'call', 'email', 'chat', 'ticket'
    subject VARCHAR(500),
    description TEXT,
    status VARCHAR(50), -- 'open', 'in_progress', 'resolved', 'closed'
    priority VARCHAR(20), -- 'low', 'medium', 'high', 'urgent'
    resolution TEXT,
    satisfaction_rating INTEGER, -- 1-5
    interaction_date TIMESTAMP NOT NULL,
    resolved_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wishlist items
CREATE TABLE wishlist_items (
    wishlist_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    product_id INTEGER REFERENCES products(product_id),
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    priority INTEGER DEFAULT 0,
    notes TEXT,
    UNIQUE(customer_id, product_id)
);

-- Shopping Cart (for abandoned cart analysis)
CREATE TABLE cart_items (
    cart_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(customer_id, product_id, is_active)
);

-- =====================================================
-- PROMOTIONS & MARKETING
-- =====================================================

-- Promotions table
CREATE TABLE promotions (
    promotion_id SERIAL PRIMARY KEY,
    promotion_name VARCHAR(200) NOT NULL,
    promotion_code VARCHAR(50) UNIQUE,
    description TEXT,
    discount_type VARCHAR(20), -- 'percentage', 'fixed_amount', 'free_shipping'
    discount_value DECIMAL(10, 2),
    min_purchase_amount DECIMAL(10, 2) DEFAULT 0,
    max_discount_amount DECIMAL(10, 2),
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    usage_limit INTEGER,
    times_used INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES employees(employee_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- ORDERS & TRANSACTIONS
-- =====================================================

-- Orders table (expanded)
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE,
    customer_id INTEGER REFERENCES customers(customer_id),
    employee_id INTEGER REFERENCES employees(employee_id), -- Sales rep
    warehouse_id INTEGER REFERENCES warehouses(warehouse_id),
    order_date TIMESTAMP NOT NULL,
    order_status VARCHAR(50) NOT NULL, -- 'pending', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded'
    total_amount DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    shipping_cost DECIMAL(10, 2) DEFAULT 0,
    payment_method VARCHAR(50),
    payment_status VARCHAR(50), -- 'pending', 'completed', 'failed', 'refunded'
    shipping_country VARCHAR(100),
    shipping_region VARCHAR(100),
    shipping_city VARCHAR(100),
    shipping_postal_code VARCHAR(20),
    shipping_address TEXT,
    billing_address TEXT,
    expected_delivery_date DATE,
    actual_delivery_date DATE,
    notes TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order items table
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    tax_amount DECIMAL(10, 2) DEFAULT 0,
    subtotal DECIMAL(10, 2) NOT NULL,
    cost_at_time DECIMAL(10, 2), -- Product cost at time of order
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Order-Promotions relationship (many-to-many)
CREATE TABLE order_promotions (
    order_promotion_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    promotion_id INTEGER REFERENCES promotions(promotion_id),
    discount_applied DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(order_id, promotion_id)
);

-- Add FK for loyalty transactions
ALTER TABLE loyalty_transactions ADD CONSTRAINT fk_loyalty_order
    FOREIGN KEY (order_id) REFERENCES orders(order_id);

-- Payment Transactions table
CREATE TABLE payment_transactions (
    transaction_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    transaction_reference VARCHAR(200) UNIQUE,
    payment_method VARCHAR(50),
    payment_provider VARCHAR(100), -- 'Stripe', 'PayPal', 'Bank', etc.
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50), -- 'pending', 'completed', 'failed', 'refunded'
    transaction_date TIMESTAMP NOT NULL,
    processed_date TIMESTAMP,
    failure_reason TEXT,
    provider_fee DECIMAL(10, 2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- SHIPPING & FULFILLMENT
-- =====================================================

-- Shipments table
CREATE TABLE shipments (
    shipment_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    warehouse_id INTEGER REFERENCES warehouses(warehouse_id),
    tracking_number VARCHAR(200),
    carrier VARCHAR(100), -- 'FedEx', 'UPS', 'USPS', 'DHL', etc.
    shipping_method VARCHAR(100), -- 'standard', 'express', 'overnight'
    shipment_status VARCHAR(50), -- 'pending', 'picked', 'packed', 'shipped', 'in_transit', 'delivered', 'failed'
    ship_date TIMESTAMP,
    estimated_delivery TIMESTAMP,
    actual_delivery TIMESTAMP,
    weight_kg DECIMAL(8, 3),
    shipping_cost DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shipment Tracking (detailed tracking events)
CREATE TABLE shipment_tracking (
    tracking_id SERIAL PRIMARY KEY,
    shipment_id INTEGER REFERENCES shipments(shipment_id),
    location VARCHAR(200),
    status VARCHAR(100),
    description TEXT,
    event_date TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- RETURNS & REFUNDS
-- =====================================================

-- Returns table
CREATE TABLE returns (
    return_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    customer_id INTEGER REFERENCES customers(customer_id),
    return_number VARCHAR(50) UNIQUE,
    return_date TIMESTAMP NOT NULL,
    reason VARCHAR(200),
    status VARCHAR(50), -- 'requested', 'approved', 'received', 'refunded', 'rejected'
    refund_amount DECIMAL(10, 2),
    restocking_fee DECIMAL(10, 2) DEFAULT 0,
    approved_by INTEGER REFERENCES employees(employee_id),
    processed_by INTEGER REFERENCES employees(employee_id),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Return Items table
CREATE TABLE return_items (
    return_item_id SERIAL PRIMARY KEY,
    return_id INTEGER REFERENCES returns(return_id),
    order_item_id INTEGER REFERENCES order_items(order_item_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    reason VARCHAR(200),
    condition VARCHAR(50), -- 'new', 'opened', 'used', 'damaged'
    refund_amount DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- REVIEWS & RATINGS
-- =====================================================

-- Reviews table
CREATE TABLE reviews (
    review_id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(product_id),
    customer_id INTEGER REFERENCES customers(customer_id),
    order_id INTEGER REFERENCES orders(order_id),
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title VARCHAR(200),
    review_text TEXT,
    is_verified_purchase BOOLEAN DEFAULT FALSE,
    helpful_count INTEGER DEFAULT 0,
    not_helpful_count INTEGER DEFAULT 0,
    is_approved BOOLEAN DEFAULT FALSE,
    reviewed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(product_id, customer_id, order_id)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Employee indexes
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_employees_hire_date ON employees(hire_date);

-- Product indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_sku ON products(sku);
CREATE INDEX idx_products_is_featured ON products(is_featured);
CREATE INDEX idx_products_price ON products(price);

-- Inventory indexes
CREATE INDEX idx_inventory_product ON inventory(product_id);
CREATE INDEX idx_inventory_warehouse ON inventory(warehouse_id);
CREATE INDEX idx_inventory_quantity ON inventory(available_quantity);

-- Customer indexes
CREATE INDEX idx_customers_segment ON customers(customer_segment);
CREATE INDEX idx_customers_country ON customers(country);
CREATE INDEX idx_customers_signup_date ON customers(signup_date);
CREATE INDEX idx_customers_loyalty_tier ON customers(loyalty_tier);
CREATE INDEX idx_customers_email ON customers(email);

-- Order indexes
CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_employee ON orders(employee_id);
CREATE INDEX idx_orders_warehouse ON orders(warehouse_id);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_payment_status ON orders(payment_status);
CREATE INDEX idx_orders_number ON orders(order_number);

-- Order items indexes
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Shipment indexes
CREATE INDEX idx_shipments_order ON shipments(order_id);
CREATE INDEX idx_shipments_tracking ON shipments(tracking_number);
CREATE INDEX idx_shipments_status ON shipments(shipment_status);
CREATE INDEX idx_shipments_ship_date ON shipments(ship_date);

-- Review indexes
CREATE INDEX idx_reviews_product ON reviews(product_id);
CREATE INDEX idx_reviews_customer ON reviews(customer_id);
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_date ON reviews(reviewed_date);

-- Payment transaction indexes
CREATE INDEX idx_payments_order ON payment_transactions(order_id);
CREATE INDEX idx_payments_status ON payment_transactions(status);
CREATE INDEX idx_payments_date ON payment_transactions(transaction_date);

-- Return indexes
CREATE INDEX idx_returns_order ON returns(order_id);
CREATE INDEX idx_returns_customer ON returns(customer_id);
CREATE INDEX idx_returns_status ON returns(status);
CREATE INDEX idx_returns_date ON returns(return_date);

-- Loyalty indexes
CREATE INDEX idx_loyalty_customer ON loyalty_transactions(customer_id);
CREATE INDEX idx_loyalty_date ON loyalty_transactions(transaction_date);

-- Interaction indexes
CREATE INDEX idx_interactions_customer ON customer_interactions(customer_id);
CREATE INDEX idx_interactions_employee ON customer_interactions(employee_id);
CREATE INDEX idx_interactions_status ON customer_interactions(status);
CREATE INDEX idx_interactions_date ON customer_interactions(interaction_date);

-- =====================================================
-- ANALYTICAL VIEWS
-- =====================================================

-- Monthly Revenue View
CREATE OR REPLACE VIEW monthly_revenue AS
SELECT
    DATE_TRUNC('month', order_date) AS month,
    COUNT(*) AS total_orders,
    SUM(total_amount) AS revenue,
    AVG(total_amount) AS avg_order_value,
    SUM(discount_amount) AS total_discounts,
    SUM(tax_amount) AS total_tax,
    SUM(shipping_cost) AS total_shipping,
    COUNT(DISTINCT customer_id) AS unique_customers
FROM orders
WHERE order_status IN ('processing', 'shipped', 'delivered')
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY month DESC;

-- Customer Lifetime Value
CREATE OR REPLACE VIEW customer_metrics AS
SELECT
    c.customer_id,
    c.customer_name,
    c.email,
    c.customer_segment,
    c.loyalty_tier,
    c.country,
    c.signup_date,
    COUNT(o.order_id) AS total_orders,
    SUM(CASE WHEN o.order_status IN ('processing', 'shipped', 'delivered')
        THEN o.total_amount ELSE 0 END) AS lifetime_value,
    AVG(CASE WHEN o.order_status IN ('processing', 'shipped', 'delivered')
        THEN o.total_amount ELSE NULL END) AS avg_order_value,
    MAX(o.order_date) AS last_order_date,
    MIN(o.order_date) AS first_order_date,
    COUNT(CASE WHEN o.order_status = 'cancelled' THEN 1 END) AS cancelled_orders,
    COUNT(r.return_id) AS total_returns
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
LEFT JOIN returns r ON c.customer_id = r.customer_id
GROUP BY c.customer_id, c.customer_name, c.email, c.customer_segment,
         c.loyalty_tier, c.country, c.signup_date;

-- Product Performance
CREATE OR REPLACE VIEW product_performance AS
SELECT
    p.product_id,
    p.product_name,
    p.sku,
    p.brand,
    c.category_name,
    p.price,
    p.cost,
    (p.price - p.cost) AS profit_per_unit,
    ROUND(((p.price - p.cost) / NULLIF(p.price, 0) * 100), 2) AS profit_margin_pct,
    SUM(i.quantity) AS total_stock,
    COUNT(DISTINCT oi.order_id) AS times_ordered,
    SUM(oi.quantity) AS total_quantity_sold,
    SUM(oi.subtotal) AS total_revenue,
    SUM(oi.quantity * (oi.unit_price - COALESCE(p.cost, 0))) AS total_profit,
    AVG(r.rating) AS avg_rating,
    COUNT(r.review_id) AS review_count
FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN inventory i ON p.product_id = i.product_id
LEFT JOIN order_items oi ON p.product_id = oi.product_id
LEFT JOIN reviews r ON p.product_id = r.product_id
GROUP BY p.product_id, p.product_name, p.sku, p.brand, c.category_name,
         p.price, p.cost;

-- Employee Sales Performance
CREATE OR REPLACE VIEW employee_sales_performance AS
SELECT
    e.employee_id,
    e.employee_name,
    e.position,
    d.department_name,
    COUNT(o.order_id) AS total_orders,
    SUM(o.total_amount) AS total_sales,
    AVG(o.total_amount) AS avg_order_value,
    SUM(o.total_amount * COALESCE(e.commission_rate, 0)) AS total_commission,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    RANK() OVER (PARTITION BY d.department_id ORDER BY SUM(o.total_amount) DESC) AS dept_rank
FROM employees e
LEFT JOIN departments d ON e.department_id = d.department_id
LEFT JOIN orders o ON e.employee_id = o.employee_id
WHERE e.position LIKE '%Sales%' OR e.position LIKE '%Representative%'
GROUP BY e.employee_id, e.employee_name, e.position, d.department_name,
         d.department_id, e.commission_rate;

-- Warehouse Performance
CREATE OR REPLACE VIEW warehouse_performance AS
SELECT
    w.warehouse_id,
    w.warehouse_name,
    w.country,
    w.city,
    COUNT(DISTINCT i.product_id) AS products_stocked,
    SUM(i.quantity) AS total_inventory,
    SUM(i.available_quantity) AS available_inventory,
    COUNT(o.order_id) AS orders_fulfilled,
    SUM(o.total_amount) AS total_revenue,
    COUNT(s.shipment_id) AS total_shipments
FROM warehouses w
LEFT JOIN inventory i ON w.warehouse_id = i.warehouse_id
LEFT JOIN orders o ON w.warehouse_id = o.warehouse_id
LEFT JOIN shipments s ON w.warehouse_id = s.warehouse_id
GROUP BY w.warehouse_id, w.warehouse_name, w.country, w.city;

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE departments IS 'Company departments and organizational structure';
COMMENT ON TABLE employees IS 'Employee master data with performance metrics';
COMMENT ON TABLE warehouses IS 'Warehouse locations and capacity information';
COMMENT ON TABLE categories IS 'Hierarchical product categories';
COMMENT ON TABLE products IS 'Product catalog with detailed specifications';
COMMENT ON TABLE suppliers IS 'Supplier master data';
COMMENT ON TABLE product_suppliers IS 'Product-supplier relationships and pricing';
COMMENT ON TABLE inventory IS 'Product inventory by warehouse location';
COMMENT ON TABLE customers IS 'Customer master data with segmentation';
COMMENT ON TABLE loyalty_transactions IS 'Customer loyalty points tracking';
COMMENT ON TABLE customer_interactions IS 'Customer service interactions and tickets';
COMMENT ON TABLE wishlist_items IS 'Customer product wishlists';
COMMENT ON TABLE cart_items IS 'Shopping cart items for abandoned cart analysis';
COMMENT ON TABLE promotions IS 'Marketing promotions and discount campaigns';
COMMENT ON TABLE orders IS 'Order transactions with shipping details';
COMMENT ON TABLE order_items IS 'Individual line items within orders';
COMMENT ON TABLE order_promotions IS 'Promotions applied to orders';
COMMENT ON TABLE payment_transactions IS 'Payment transaction log';
COMMENT ON TABLE shipments IS 'Shipment tracking information';
COMMENT ON TABLE shipment_tracking IS 'Detailed shipment tracking events';
COMMENT ON TABLE returns IS 'Product return requests';
COMMENT ON TABLE return_items IS 'Individual items being returned';
COMMENT ON TABLE reviews IS 'Product reviews and ratings';

COMMENT ON VIEW monthly_revenue IS 'Monthly revenue and order statistics';
COMMENT ON VIEW customer_metrics IS 'Customer lifetime value and engagement metrics';
COMMENT ON VIEW product_performance IS 'Product sales, profit, and rating metrics';
COMMENT ON VIEW employee_sales_performance IS 'Employee sales performance and rankings';
COMMENT ON VIEW warehouse_performance IS 'Warehouse inventory and fulfillment metrics';
