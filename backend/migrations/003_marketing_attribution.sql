CREATE TABLE IF NOT EXISTS campaign_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    campaign_name VARCHAR(150) NOT NULL,
    source VARCHAR(100) NOT NULL,
    ref_slug VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE campaign_links DROP CONSTRAINT IF EXISTS campaign_links_ref_slug_key;
CREATE UNIQUE INDEX IF NOT EXISTS idx_campaign_links_store_ref ON campaign_links(store_id, ref_slug);
CREATE INDEX IF NOT EXISTS idx_campaign_links_store_source ON campaign_links(store_id, source);

CREATE TABLE IF NOT EXISTS campaign_visits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaign_links(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    session_id VARCHAR(120),
    visited_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_campaign_visits_campaign_time ON campaign_visits(campaign_id, visited_at);
CREATE UNIQUE INDEX IF NOT EXISTS idx_campaign_visits_session_once
    ON campaign_visits(campaign_id, session_id)
    WHERE session_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS campaign_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaign_links(id) ON DELETE CASCADE NOT NULL,
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE NOT NULL,
    product_id UUID REFERENCES products(id) ON DELETE SET NULL,
    session_id VARCHAR(120),
    event_type VARCHAR(40) NOT NULL CHECK (event_type IN ('product_view', 'add_to_cart')),
    occurred_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_campaign_events_campaign_type_time
    ON campaign_events(campaign_id, event_type, occurred_at);

CREATE TABLE IF NOT EXISTS campaign_conversions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES campaign_links(id) ON DELETE CASCADE NOT NULL,
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE NOT NULL,
    revenue NUMERIC(12,2) NOT NULL,
    converted_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_campaign_conversions_order ON campaign_conversions(order_id);
CREATE INDEX IF NOT EXISTS idx_campaign_conversions_campaign_time
    ON campaign_conversions(campaign_id, converted_at);

ALTER TABLE orders ADD COLUMN IF NOT EXISTS campaign_ref VARCHAR(100);
