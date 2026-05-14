-- Migration: 002_storefront.sql
-- Adds storefront tables: stores, products, orders, order_items, inventory_movements

-- Ensure uuid extension exists (safe if already created)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_name VARCHAR(150) NOT NULL,
    slug VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    logo_url VARCHAR(1024),
    theme_json JSONB,
    contact_whatsapp VARCHAR(40),
    business_category VARCHAR(120),
    pickup_delivery_note TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price NUMERIC(12,2) NOT NULL DEFAULT 0,
    image_url VARCHAR(1024),
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    customer_name VARCHAR(200),
    customer_phone VARCHAR(40),
    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    payment_status VARCHAR(30) DEFAULT 'pending',
    order_status VARCHAR(30) DEFAULT 'pending',
    squad_payment_reference VARCHAR(200),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0,
    total_price NUMERIC(14,2) GENERATED ALWAYS AS (quantity * unit_price) STORED
);

CREATE TABLE inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE CASCADE NOT NULL,
    movement_type VARCHAR(30) NOT NULL, -- stock_added, stock_removed, manual_adjustment, order_paid, order_cancelled
    quantity INTEGER NOT NULL,
    reason TEXT,
    related_order_id UUID REFERENCES orders(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_stores_user ON stores(user_id);
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_orders_store ON orders(store_id);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_inventory_movements_product ON inventory_movements(product_id);
