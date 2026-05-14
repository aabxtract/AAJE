ALTER TABLE users ADD COLUMN IF NOT EXISTS persona_mode VARCHAR(40) DEFAULT 'normal_business_manager';
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255) UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS whatsapp_connected BOOLEAN DEFAULT FALSE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS business_description TEXT;
ALTER TABLE users ALTER COLUMN whatsapp_no DROP NOT NULL;

CREATE TABLE IF NOT EXISTS stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_name VARCHAR(150) NOT NULL,
    slug VARCHAR(180) UNIQUE NOT NULL CHECK (slug = lower(slug) AND slug ~ '^[a-z0-9][a-z0-9-]*$'),
    store_slug VARCHAR(180) UNIQUE,
    description TEXT,
    store_description TEXT,
    tagline VARCHAR(255),
    theme_json JSONB DEFAULT '{}'::jsonb,
    theme VARCHAR(50) DEFAULT 'default',
    contact_whatsapp VARCHAR(20),
    whatsapp_number VARCHAR(20),
    squad_virtual_account_id VARCHAR(100),
    squad_virtual_account_number VARCHAR(20),
    squad_customer_identifier VARCHAR(120) UNIQUE,
    has_squad_account BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS store_slug VARCHAR(180) UNIQUE;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS store_description TEXT;
ALTER TABLE stores ADD COLUMN IF NOT EXISTS theme VARCHAR(50) DEFAULT 'default';
ALTER TABLE stores ADD COLUMN IF NOT EXISTS whatsapp_number VARCHAR(20);
ALTER TABLE stores ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_stores_slug_lowercase'
    ) THEN
        ALTER TABLE stores
            ADD CONSTRAINT ck_stores_slug_lowercase CHECK (slug = lower(slug)) NOT VALID;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'ck_stores_slug_url_safe'
    ) THEN
        ALTER TABLE stores
            ADD CONSTRAINT ck_stores_slug_url_safe CHECK (slug ~ '^[a-z0-9][a-z0-9-]*$') NOT VALID;
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    price NUMERIC(12,2) NOT NULL,
    image_url TEXT,
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 5,
    is_active BOOLEAN DEFAULT TRUE,
    is_available BOOLEAN DEFAULT TRUE,
    source VARCHAR(20) DEFAULT 'web',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
ALTER TABLE products ADD COLUMN IF NOT EXISTS user_id UUID REFERENCES users(id) ON DELETE CASCADE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_available BOOLEAN DEFAULT TRUE;
ALTER TABLE products ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'web';
ALTER TABLE products ADD COLUMN IF NOT EXISTS type VARCHAR(20) DEFAULT 'product';

CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    customer_name VARCHAR(120),
    customer_phone VARCHAR(20),
    customer_whatsapp VARCHAR(20),
    total_amount NUMERIC(12,2) NOT NULL,
    payment_status VARCHAR(30) DEFAULT 'pending',
    order_status VARCHAR(30) DEFAULT 'pending',
    status VARCHAR(20) DEFAULT 'pending',
    squad_payment_reference VARCHAR(120) UNIQUE,
    squad_transaction_ref VARCHAR(100),
    payment_method VARCHAR(20) DEFAULT 'transfer',
    notes TEXT,
    idempotency_key VARCHAR(120) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    paid_at TIMESTAMPTZ
);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_whatsapp VARCHAR(20);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'pending';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS squad_transaction_ref VARCHAR(100);
ALTER TABLE orders ADD COLUMN IF NOT EXISTS payment_method VARCHAR(20) DEFAULT 'transfer';
ALTER TABLE orders ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE orders ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) NOT NULL,
    product_name VARCHAR(200),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    total_price NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL
);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS product_name VARCHAR(200);
ALTER TABLE order_items ADD COLUMN IF NOT EXISTS subtotal NUMERIC(12,2);

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

ALTER TABLE transactions ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS order_id UUID REFERENCES orders(id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS stream_id UUID REFERENCES income_streams(id);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS external_reference VARCHAR(120);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS provider VARCHAR(50);
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS status VARCHAR(30) DEFAULT 'completed';
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS raw_payload TEXT;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS narration TEXT;
ALTER TABLE transactions ADD COLUMN IF NOT EXISTS squad_transaction_ref VARCHAR(100);
CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_ref_unique ON transactions(squad_transaction_ref);

ALTER TABLE vaults ADD COLUMN IF NOT EXISTS store_id UUID REFERENCES stores(id);
ALTER TABLE vaults ADD COLUMN IF NOT EXISTS name VARCHAR(120) DEFAULT 'Main Vault';
ALTER TABLE vaults ADD COLUMN IF NOT EXISTS percentage NUMERIC(5,2) DEFAULT 0;
ALTER TABLE vaults ADD COLUMN IF NOT EXISTS is_default BOOLEAN DEFAULT FALSE;

ALTER TABLE scores ADD COLUMN IF NOT EXISTS data_quality VARCHAR(30) DEFAULT 'low';

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(80) NOT NULL,
    source VARCHAR(60) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id),
    payload_json JSONB DEFAULT '{}'::jsonb,
    processed BOOLEAN DEFAULT FALSE,
    idempotency_key VARCHAR(160) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ledger_entries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id),
    vault_id UUID REFERENCES vaults(id),
    direction VARCHAR(10) NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    currency VARCHAR(5) DEFAULT 'NGN',
    reference VARCHAR(120) NOT NULL,
    source VARCHAR(60) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS flow_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    token_hash VARCHAR(128) UNIQUE NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    flow_type VARCHAR(80) NOT NULL,
    payload_json JSONB DEFAULT '{}'::jsonb,
    expires_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(30) DEFAULT 'open',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS consents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    consent_type VARCHAR(80) NOT NULL,
    institution_id VARCHAR(120),
    token_hash VARCHAR(128) UNIQUE,
    scopes JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS score_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    score NUMERIC(8,2) NOT NULL,
    grade VARCHAR(5),
    factors_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bizprint_snapshots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id),
    data_quality VARCHAR(30) DEFAULT 'low',
    snapshot_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    actor VARCHAR(120) NOT NULL,
    action VARCHAR(120) NOT NULL,
    target_type VARCHAR(80),
    target_id VARCHAR(120),
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS virtual_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    account_name VARCHAR(100),
    account_number VARCHAR(20) UNIQUE,
    squad_account_id VARCHAR(100),
    bank_name VARCHAR(100) DEFAULT 'GTBank',
    is_primary BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    available_balance NUMERIC(12,2) DEFAULT 0,
    total_earned NUMERIC(12,2) DEFAULT 0,
    total_withdrawn NUMERIC(12,2) DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    alias VARCHAR(100),
    bank_name VARCHAR(100),
    bank_code VARCHAR(10),
    account_number VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS mono_transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    amount NUMERIC(12,2),
    type VARCHAR(10),
    narration TEXT,
    date TIMESTAMPTZ,
    mono_id VARCHAR(100) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS failed_transfers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    destination_json TEXT,
    reference VARCHAR(120) UNIQUE,
    error_message TEXT,
    retry_count NUMERIC(3,0) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_stores_user ON stores(user_id);
CREATE INDEX IF NOT EXISTS idx_stores_slug ON stores(slug);
CREATE INDEX IF NOT EXISTS idx_stores_store_slug ON stores(store_slug);
CREATE INDEX IF NOT EXISTS idx_products_store ON products(store_id);
CREATE INDEX IF NOT EXISTS idx_orders_store ON orders(store_id);
CREATE INDEX IF NOT EXISTS idx_events_user ON events(user_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_ledger_user ON ledger_entries(user_id);
CREATE INDEX IF NOT EXISTS idx_wallets_user ON wallets(user_id);
CREATE INDEX IF NOT EXISTS idx_virtual_accounts_user ON virtual_accounts(user_id);
