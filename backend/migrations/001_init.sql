CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    whatsapp_no VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    location VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en',
    pin_hash VARCHAR(255),
    verified_bank_account VARCHAR(20),
    verified_bank_code VARCHAR(10),
    verified_bank_name VARCHAR(100),
    squad_customer_id VARCHAR(100),
    mono_account_id VARCHAR(100),
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE income_streams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stream_name VARCHAR(100) NOT NULL,
    stream_type VARCHAR(50),
    squad_account_id VARCHAR(100),
    squad_account_number VARCHAR(20),
    split_percentage NUMERIC(5,2),
    is_savings BOOLEAN DEFAULT FALSE,
    is_emergency BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stream_id UUID REFERENCES income_streams(id),
    amount NUMERIC(12,2) NOT NULL,
    type VARCHAR(10) CHECK (type IN ('credit', 'debit')),
    narration TEXT,
    category VARCHAR(50),
    source VARCHAR(50),
    squad_transaction_ref VARCHAR(100) UNIQUE,
    timestamp TIMESTAMPTZ NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE vaults (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    stream_id UUID REFERENCES income_streams(id) UNIQUE,
    current_balance NUMERIC(12,2) DEFAULT 0,
    total_deposited NUMERIC(12,2) DEFAULT 0,
    total_withdrawn NUMERIC(12,2) DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    trader_score FLOAT DEFAULT 0,
    credit_grade VARCHAR(5),
    consistency_score FLOAT DEFAULT 0,
    volume_score FLOAT DEFAULT 0,
    savings_score FLOAT DEFAULT 0,
    tenure_score FLOAT DEFAULT 0,
    recommended_loan_ceiling NUMERIC(14,2),
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_stream ON transactions(stream_id);
CREATE INDEX idx_transactions_ref ON transactions(squad_transaction_ref);
CREATE INDEX idx_income_streams_user ON income_streams(user_id);
CREATE INDEX idx_vaults_stream ON vaults(stream_id);
CREATE INDEX idx_scores_user ON scores(user_id);
CREATE INDEX idx_users_whatsapp ON users(whatsapp_no);
