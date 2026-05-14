-- Migration: 004_platform_schema_backfill.sql
-- Backfills the hosted Postgres schema for the AI-native storefront backend.
-- This is additive and keeps legacy AAJE data in place.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'email';
ALTER TABLE users ADD COLUMN IF NOT EXISTS plan VARCHAR(50) DEFAULT 'free';
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_description TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS persona_mode VARCHAR(40) DEFAULT 'normal_business_manager';
ALTER TABLE users ALTER COLUMN whatsapp_no DROP NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email) WHERE email IS NOT NULL;

CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_name VARCHAR(150) NOT NULL,
    slug VARCHAR(180) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE stores ADD COLUMN IF NOT EXISTS store_slug VARCHAR(180);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS store_description TEXT;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS tagline VARCHAR(255);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS layout VARCHAR(80) DEFAULT 'clean_minimal';
ALTER TABLE stores ADD COLUMN IF NOT EXISTS theme_json JSONB DEFAULT '{}'::jsonb;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS theme VARCHAR(50) DEFAULT 'default';
ALTER TABLE stores ADD COLUMN IF NOT EXISTS contact_whatsapp VARCHAR(20);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS squad_virtual_account_id VARCHAR(100);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS squad_virtual_account_number VARCHAR(20);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS squad_customer_identifier VARCHAR(120);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS has_squad_account BOOLEAN DEFAULT FALSE;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS is_published BOOLEAN DEFAULT FALSE;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE UNIQUE INDEX IF NOT EXISTS idx_stores_store_slug ON stores(store_slug) WHERE store_slug IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_stores_user ON stores(user_id);

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    name VARCHAR(150) NOT NULL,
    price NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE products ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS category VARCHAR(100);
ALTER TABLE products ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'product';
ALTER TABLE products ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE products ADD COLUMN IF NOT EXISTS stock_quantity INTEGER DEFAULT 0;
ALTER TABLE products ADD COLUMN IF NOT EXISTS low_stock_threshold INTEGER DEFAULT 5;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_available BOOLEAN DEFAULT TRUE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'web';
ALTER TABLE products ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_products_store ON products(store_id);

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    total_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE orders ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_name VARCHAR(120);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_phone VARCHAR(20);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_whatsapp VARCHAR(20);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS order_status VARCHAR(30) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS squad_payment_reference VARCHAR(120);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS squad_transaction_ref VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'transfer';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS campaign_ref VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS campaign_source VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(120);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE orders ADD COLUMN IF NOT EXISTS paid_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_orders_store ON orders(store_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_orders_idempotency_key ON orders(idempotency_key) WHERE idempotency_key IS NOT NULL;

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    unit_price NUMERIC(12,2) NOT NULL DEFAULT 0
);

ALTER TABLE order_items ADD COLUMN IF NOT EXISTS product_name VARCHAR(200);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS total_price NUMERIC(12,2);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM pg_attribute
        WHERE attrelid = 'order_items'::regclass
          AND attname = 'total_price'
          AND attgenerated <> ''
    ) THEN
        ALTER TABLE order_items ALTER COLUMN total_price DROP EXPRESSION;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);

CREATE TABLE IF NOT EXISTS inventory_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) NOT NULL,
    movement_type VARCHAR(30) NOT NULL,
    quantity INTEGER NOT NULL,
    reason VARCHAR(120),
    related_order_id UUID REFERENCES orders(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inventory_movements_product ON inventory_movements(product_id);

ALTER TABLE transactions ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS order_id UUID REFERENCES orders(id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS external_reference VARCHAR(120);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'completed';
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS raw_payload TEXT;

CREATE TABLE IF NOT EXISTS whatsapp_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    phone VARCHAR(20),
    daily_notification_time VARCHAR(10) DEFAULT '20:00',
    is_enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    plan_name VARCHAR(50) DEFAULT 'free',
    status VARCHAR(30) DEFAULT 'active',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS bizprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    score NUMERIC(8,2) DEFAULT 0,
    label VARCHAR(80),
    breakdown_json JSONB DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
