-- Migration 001: Initial Schema
-- Run in Supabase SQL Editor

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    whatsapp_no VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    location VARCHAR(100),
    business_type VARCHAR(50),
    preferred_language VARCHAR(10) DEFAULT 'en',
    pin_hash VARCHAR(255),
    trader_score FLOAT DEFAULT 0,
    mono_account_id VARCHAR(100),
    verified_bank_account VARCHAR(20),
    verified_bank_code VARCHAR(10),
    verified_bank_name VARCHAR(100),
    squad_customer_id VARCHAR(100),
    squad_virtual_accounts JSONB DEFAULT '{}',
    slice_config JSONB DEFAULT '{}',
    daily_debrief_time TIME DEFAULT '20:00:00',
    last_synced_at TIMESTAMPTZ,
    onboarding_stage VARCHAR(30) DEFAULT 'NEW',
    onboarding_complete BOOLEAN DEFAULT FALSE,
    policies_accepted_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('credit', 'debit')),
    category VARCHAR(50),
    description TEXT,
    source VARCHAR(20) CHECK (source IN ('mono', 'ocr', 'manual')),
    mono_transaction_id VARCHAR(100) UNIQUE,
    timestamp TIMESTAMPTZ NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vault_movements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    source_transaction_id UUID REFERENCES transactions(id),
    vault_name VARCHAR(50),
    amount NUMERIC(12,2) NOT NULL,
    direction VARCHAR(10) CHECK (direction IN ('in', 'out')),
    squad_transfer_ref VARCHAR(100),
    fee_charged NUMERIC(6,2) DEFAULT 5.00,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE withdrawals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    from_vault VARCHAR(50),
    amount NUMERIC(12,2) NOT NULL,
    destination_account VARCHAR(20),
    squad_transfer_ref VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    initiated_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    alias VARCHAR(50),
    bank_name VARCHAR(100),
    bank_code VARCHAR(10),
    account_number VARCHAR(20),
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    supplier_id UUID REFERENCES suppliers(id),
    from_vault VARCHAR(50),
    amount NUMERIC(12,2) NOT NULL,
    squad_transfer_ref VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    raw_image_url TEXT,
    extracted_data JSONB,
    linked_transaction_id UUID REFERENCES transactions(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE escalations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    trigger_message TEXT,
    trigger_type VARCHAR(30),
    conversation_snapshot JSONB,
    status VARCHAR(20) DEFAULT 'open',
    admin_notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(30),
    delivered_at TIMESTAMPTZ DEFAULT NOW(),
    content_summary TEXT
);

-- Indexes
CREATE INDEX idx_transactions_user_timestamp
    ON transactions(user_id, timestamp DESC);
CREATE INDEX idx_transactions_mono_id
    ON transactions(mono_transaction_id);
CREATE INDEX idx_vault_movements_user
    ON vault_movements(user_id);
CREATE INDEX idx_escalations_status
    ON escalations(status);
CREATE INDEX idx_users_whatsapp
    ON users(whatsapp_no);
