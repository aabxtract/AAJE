Perfect. Now we build.

---

## The UVP (Locked)

**"Stop managing your business in your head. AAJE puts everything in one chat."**

Tagline for the storefront: **"Your store. Your orders. Your money. One WhatsApp chat."**

---

## What AAJE Is (Locked Definition)

AAJE is a WhatsApp-native business operating system for offline traders and social commerce sellers. It gives them a live AI-generated storefront, automated order management, payment collection via Monnify, and a financial identity score — all managed through a single WhatsApp conversation.

---

## The Full Tech Stack (Locked)

```
Backend          Python 3.11 + FastAPI
                 Async throughout
                 Hosted on Railway (free tier, better DX than Render for FastAPI)
                 or Render — your call

Database         PostgreSQL via Supabase (free tier)

Cache/Session    Upstash Redis (free tier)

WhatsApp         Meta WhatsApp Cloud API (free tier)

Payments         Monnify API
                 Payment link generation per order
                 Webhook for payment confirmation

AI — LLM         Groq / Llama 4 Scout
                 Store generation, order categorization,
                 agent reasoning, translation, insights

AI — Storefront  Groq generates store content, layout config,
                 product descriptions, color palette suggestions
                 All rendered within AAJE's storefront infrastructure

Analytics        Pandas (BizPrint score computation)

Storage          Supabase Storage (product images)

Scheduling       APScheduler (weekly BizPrint, daily summaries)

Frontend         Vanilla HTML + CSS + JS for storefront
                 Chart.js from CDN for analytics
                 Deployed on Vercel (free tier)

WhatsApp Flows   Meta Flows for PIN entry, order details,
                 BizPrint view, withdrawal

Auth             JWT via python-jose
                 bcrypt for passwords and PINs
```

---

## The Complete Database Schema

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ─────────────────────────────────────────
-- USERS
-- ─────────────────────────────────────────
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    whatsapp_no VARCHAR(20) UNIQUE,
    whatsapp_connected BOOLEAN DEFAULT FALSE,
    whatsapp_verified BOOLEAN DEFAULT FALSE,
    preferred_language VARCHAR(10) DEFAULT 'en',
    location VARCHAR(100),
    business_description TEXT,
    pin_hash VARCHAR(255),
    onboarding_complete BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- STORES
-- ─────────────────────────────────────────
CREATE TABLE stores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    store_name VARCHAR(100) NOT NULL,
    store_slug VARCHAR(100) UNIQUE NOT NULL,
    store_description TEXT,
    whatsapp_number VARCHAR(20),
    -- customer-facing contact number
    theme_config JSONB DEFAULT '{}',
    -- AI-generated: colors, fonts, layout
    logo_url TEXT,
    banner_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- PRODUCTS
-- ─────────────────────────────────────────
CREATE TABLE products (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    price NUMERIC(12,2) NOT NULL,
    category VARCHAR(100),
    image_url TEXT,
    stock_count INTEGER,
    -- NULL means unlimited
    is_available BOOLEAN DEFAULT TRUE,
    source VARCHAR(20) DEFAULT 'web',
    -- 'web' or 'whatsapp'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- ORDERS
-- ─────────────────────────────────────────
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    store_id UUID REFERENCES stores(id),
    user_id UUID REFERENCES users(id),
    order_ref VARCHAR(20) UNIQUE NOT NULL,
    -- human readable: AAJE-2026-0001
    customer_name VARCHAR(100),
    customer_whatsapp VARCHAR(20),
    customer_email VARCHAR(255),
    total_amount NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    -- pending, paid, processing,
    -- delivered, cancelled, refunded
    payment_status VARCHAR(20) DEFAULT 'unpaid',
    -- unpaid, paid, failed
    monnify_payment_ref VARCHAR(100),
    monnify_transaction_ref VARCHAR(100),
    payment_link TEXT,
    -- Monnify payment link URL
    notes TEXT,
    delivery_address TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- ORDER ITEMS
-- ─────────────────────────────────────────
CREATE TABLE order_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    product_name VARCHAR(200) NOT NULL,
    -- snapshot at time of order
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    subtotal NUMERIC(12,2) NOT NULL
);

-- ─────────────────────────────────────────
-- WALLET
-- ─────────────────────────────────────────
CREATE TABLE wallets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    available_balance NUMERIC(12,2) DEFAULT 0,
    total_earned NUMERIC(12,2) DEFAULT 0,
    total_orders_paid INTEGER DEFAULT 0,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- TRANSACTIONS
-- ─────────────────────────────────────────
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    order_id UUID REFERENCES orders(id) NULLABLE,
    amount NUMERIC(12,2) NOT NULL,
    fee NUMERIC(8,2) DEFAULT 0,
    net_amount NUMERIC(12,2) NOT NULL,
    type VARCHAR(20),
    -- 'order_payment', 'withdrawal',
    -- 'supplier_payment', 'refund'
    narration TEXT,
    monnify_ref VARCHAR(100),
    status VARCHAR(20) DEFAULT 'success',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- SUPPLIERS
-- ─────────────────────────────────────────
CREATE TABLE suppliers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    alias VARCHAR(100) NOT NULL,
    bank_name VARCHAR(100),
    bank_code VARCHAR(10),
    account_number VARCHAR(20),
    account_name VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- CONNECTED BANK ACCOUNTS
-- ─────────────────────────────────────────
CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    bank_name VARCHAR(100),
    bank_code VARCHAR(10),
    account_number VARCHAR(20),
    account_name VARCHAR(100),
    -- verified via Monnify lookup
    is_primary BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- BIZPRINT SCORES
-- ─────────────────────────────────────────
CREATE TABLE bizprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    trader_score FLOAT DEFAULT 0,
    credit_grade VARCHAR(5),
    -- A+, A, B+, B, C+, C, D
    consistency_score FLOAT DEFAULT 0,
    volume_score FLOAT DEFAULT 0,
    growth_score FLOAT DEFAULT 0,
    tenure_score FLOAT DEFAULT 0,
    recommended_loan_ceiling NUMERIC(14,2) DEFAULT 0,
    total_orders_analyzed INTEGER DEFAULT 0,
    computed_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- NOTIFICATIONS LOG
-- ─────────────────────────────────────────
CREATE TABLE notification_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    type VARCHAR(50),
    -- 'order_received', 'payment_confirmed',
    -- 'weekly_bizprint', 'daily_summary'
    content TEXT,
    delivered BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ─────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────
CREATE INDEX idx_products_store ON products(store_id);
CREATE INDEX idx_products_available ON products(store_id, is_available);
CREATE INDEX idx_orders_store ON orders(store_id);
CREATE INDEX idx_orders_status ON orders(store_id, status);
CREATE INDEX idx_orders_ref ON orders(order_ref);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_transactions_user ON transactions(user_id);
CREATE INDEX idx_transactions_monnify ON transactions(monnify_ref);
CREATE INDEX idx_users_whatsapp ON users(whatsapp_no);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_stores_slug ON stores(store_slug);
CREATE INDEX idx_bizprints_user ON bizprints(user_id);
```

---

## Complete Folder Structure

```
aaje/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── store.py
│   │   │   ├── products.py
│   │   │   ├── orders.py
│   │   │   ├── wallet.py
│   │   │   ├── bizprint.py
│   │   │   ├── webhook_monnify.py
│   │   │   ├── webhook_whatsapp.py
│   │   │   └── intelligence.py
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── monnify.py
│   │   │   ├── whatsapp_client.py
│   │   │   ├── session.py
│   │   │   ├── pin.py
│   │   │   ├── auth_service.py
│   │   │   └── store_generator.py
│   │   │
│   │   ├── intelligence/
│   │   │   ├── __init__.py
│   │   │   ├── llm.py
│   │   │   ├── agent.py
│   │   │   ├── refinery.py
│   │   │   └── pii_scrubber.py
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── onboarding_agent.py
│   │   │   ├── order_agent.py
│   │   │   ├── product_agent.py
│   │   │   ├── money_agent.py
│   │   │   └── bizprint_agent.py
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── store.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   ├── order_item.py
│   │   │   ├── wallet.py
│   │   │   ├── transaction.py
│   │   │   ├── supplier.py
│   │   │   ├── bank_account.py
│   │   │   ├── bizprint.py
│   │   │   └── notification_log.py
│   │   │
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── store.py
│   │   │   ├── product.py
│   │   │   ├── order.py
│   │   │   └── bizprint.py
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── message_parser.py
│   │       ├── formatters.py
│   │       ├── frustration.py
│   │       ├── rail_guard.py
│   │       └── order_ref.py
│   │
│   ├── migrations/
│   │   └── 001_init.sql
│   ├── scheduler.py
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── storefront/
│   ├── index.html          # Landing page
│   ├── signup.html         # Web onboarding
│   ├── dashboard.html      # Trader dashboard
│   ├── store.html          # Public store page
│   ├── orders.html         # Order management
│   ├── analytics.html      # BizPrint + revenue
│   ├── connect.html        # WhatsApp connect
│   └── assets/
│       ├── css/
│       │   ├── main.css
│       │   ├── store.css
│       │   └── dashboard.css
│       └── js/
│           ├── api.js      # All fetch calls
│           ├── auth.js
│           ├── store.js
│           ├── dashboard.js
│           ├── orders.js
│           └── analytics.js
│
└── docs/
    └── agent_knowledge.md
```

---

## The Build Phases

---

### Phase 0 — Accounts and Environment

Everything collected before code is written.

**Meta WhatsApp Cloud API** — Meta Business Account, Facebook App with WhatsApp product, free test number, system user access token that never expires, webhook verify token you create yourself. Collect: meta_app_id, meta_app_secret, meta_phone_number_id, meta_whatsapp_token, meta_webhook_verify_token.

**Monnify** — create account at monnify.com. Get API key and secret key from sandbox dashboard. Note your contract code. Create a split payment configuration if needed. Collect: monnify_api_key, monnify_secret_key, monnify_base_url, monnify_contract_code.

**Supabase** — create project. Get project URL, anon key, service role key, database URL. Create one public storage bucket named media for product images and store assets.

**Upstash** — create Redis database free tier. Get REST URL and REST Token.

**Groq** — get API key. Confirm Llama 4 Scout available.

**Vercel** — connect GitHub account for storefront deployment.

**Render or Railway** — connect GitHub for backend deployment. Railway has better free tier for FastAPI.

**GitHub** — create repo named aaje. Add teammate as collaborator. Push full folder structure immediately.

**ngrok** — install on both machines, one static domain each.

**Environment file:**

```
# Server
APP_ENV=development
SECRET_KEY=
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRY_HOURS=168
ADMIN_TOKEN=
FRONTEND_URL=http://localhost:3000

# Meta WhatsApp Cloud API
META_APP_ID=
META_APP_SECRET=
META_PHONE_NUMBER_ID=
META_WHATSAPP_TOKEN=
META_WEBHOOK_VERIFY_TOKEN=

# Monnify
MONNIFY_API_KEY=
MONNIFY_SECRET_KEY=
MONNIFY_BASE_URL=https://sandbox.monnify.com
MONNIFY_CONTRACT_CODE=

# Supabase
SUPABASE_URL=
SUPABASE_KEY=
DATABASE_URL=

# Upstash Redis
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=

# Groq
GROQ_API_KEY=
```

**Deliverable:** Every key in hand. Repo created. Both teammates added. .env.example committed. ngrok running. Monnify sandbox payment confirmed reachable.

---

### Phase 1 — Backend Foundation

Build in strict order. Nothing proceeds until the previous step is confirmed working.

**config.py** — pydantic-settings, all lowercase snake_case, reads from .env.

**database.py** — SQLAlchemy 2.0 async with asyncpg. AsyncSessionLocal. Base. get_db dependency.

**redis.py** — Upstash client. get_session(), save_session() 30 min TTL, clear_session(), increment_pin_attempts() 10 min TTL, clear_pin_attempts(), set_rate_limit() 60 sec TTL.

**All SQLAlchemy models** — one file per table. models/__init__.py imports every single model. Non-negotiable.

**Run 001_init.sql in Supabase** — confirm every table exists before writing any service code.

**schemas/** — Pydantic v2 schemas for all request and response bodies. Separate from models. auth.py has SignupRequest, LoginRequest, TokenResponse. store.py has StoreCreate, StoreResponse. product.py has ProductCreate, ProductUpdate, ProductResponse. order.py has OrderCreate, OrderResponse. bizprint.py has BizPrintResponse.

**auth_service.py** — create_access_token() using python-jose. verify_token(). get_current_user() FastAPI dependency that reads JWT from Authorization header and returns the user. hash_password() and verify_password() with passlib bcrypt.

**pin.py** — hash_pin() bcrypt cost 12. verify_pin(). is_valid_pin() rejects non-4-digit and obvious PINs. handle_pin_input() verifies PIN, routes to correct action, handles lockout after 3 wrong attempts.

**formatters.py** — format_naira(), names_match() fuzzy at 0.85, generate_order_ref() produces AAJE-YYYY-NNNN format.

**rail_guard.py** — is_financial_topic() returns True for orders, payments, products, balance, BizPrint, Nigerian economy, business advice. Returns False for everything else. False triggers standard off-topic response without reaching the agent.

**message_parser.py** — detect_intent() with keyword sets across all 5 languages. Intents: greeting, my_orders, balance, withdraw, pay_supplier, add_product, update_product, bizprint, my_store, help, menu, unknown.

**frustration.py** — detect_frustration() signal lists in all 5 languages.

**pii_scrubber.py** — scrub() strips account numbers to last 4 digits, removes password_hash, pin_hash, replaces full_name with first name, rounds monetary amounts to nearest hundred. Called before every LLM call.

**whatsapp_client.py** — httpx async calls to Meta Cloud API. send_text(), send_buttons() as list message, send_cta_button(), send_image(). All validate that meta_whatsapp_token is set. Log every non-200 response with full body.

**webhook_whatsapp.py** — GET for Meta verification, POST for incoming messages. X-Hub-Signature-256 validation using meta_app_secret. Rate limiting. BackgroundTasks for process_message. try-except wrapper — never fail silently.

**main.py** — register all routers. CORS for frontend URL. Lifespan starts scheduler. Health endpoint returns status, environment, version.

**session.py** — route_message() loads session, checks WhatsApp connection status, checks rail_guard, checks frustration, checks PIN interceptor, routes to correct agent.

**Milestone:** Start server locally with ngrok. Configure Meta webhook. Send "hi" from WhatsApp. Receive reply. Two-way confirmed.

---

### Phase 2 — Auth and Web Signup

**auth.py routes:**

POST /auth/signup — validate email uniqueness, hash password, create user record, create wallet record with zero balance, return JWT token and user data.

POST /auth/login — verify credentials, return JWT token and user data.

GET /auth/me — return current user profile from JWT.

POST /auth/connect-whatsapp — authenticated. Takes whatsapp_no. Generates a 6-digit OTP, stores in Redis with 10 minute TTL as whatsapp_otp:{user_id}, sends OTP to that WhatsApp number via whatsapp_client.send_text(). Returns confirmation that OTP was sent.

POST /auth/verify-whatsapp — authenticated. Takes whatsapp_no and otp. Checks Redis for stored OTP. On match updates users.whatsapp_no and whatsapp_verified True. Returns updated user.

PATCH /auth/set-pin — authenticated. Takes pin and confirm_pin. Validates they match. Validates pin quality. Hashes and stores. Returns success.

**store_generator.py:**

generate_store_from_description() takes the trader's raw business description string and calls Llama 4 Scout. System prompt instructs the model to extract a structured JSON object containing store_name, store_description, suggested_slug, theme_config with primary_color and accent_color and font_style, and products array each with name, suggested_price, category, and short_description. Returns the parsed JSON. On parse failure returns a safe default structure.

generate_slug() takes store_name, converts to lowercase, replaces spaces with hyphens, removes special characters, checks uniqueness against stores table, appends a number if taken.

**store.py routes:**

POST /store/setup — authenticated. Takes business_description. Calls store_generator.generate_store_from_description(). Creates store record. Creates all extracted products. Creates Monnify payment page if applicable. Returns store with all products and public URL.

GET /store/{slug} — public. Returns store with all available products. No auth. This is what customers see.

GET /store/me/dashboard — authenticated. Returns store with stats: total orders, pending orders, today's revenue, total revenue, product count.

PATCH /store/me — authenticated. Update store_name, store_description, theme_config, whatsapp_number.

POST /store/me/publish — authenticated. Sets is_published True. Store becomes publicly visible.

**storefront/signup.html:**

Clean signup form. Email, password, full name. Then a large textarea with placeholder: "Tell me about your business. What do you sell? What are your prices? (e.g. I sell rice ₦500, tomatoes ₦200 per cup, beans ₦400 and also do small catering for events)." Submit button labeled "Build My Store." On submit show a loading state with progress message "Our AI is building your store..." After response show store preview with live link and "Connect WhatsApp" prompt.

**Milestone:** Sign up on web. Type business description. AI extracts products. Store live at /store/{slug}. All products visible publicly. Wallet initialized.

---

### Phase 3 — Products and Orders

**products.py routes:**

GET /products — authenticated. All products for trader's store with availability status.

POST /products — authenticated. Create single product manually. Returns created product.

PATCH /products/{id} — authenticated. Update name, price, description, availability, image.

DELETE /products/{id} — authenticated. Soft delete — sets is_available False.

POST /products/bulk — authenticated. Create multiple products at once. Used by store generator.

**Supabase Storage for images** — POST /products/{id}/image uploads image file to Supabase public bucket, returns public URL, updates product.image_url.

**orders.py routes:**

POST /orders — public. Customer places order. Takes store_slug, customer_name, customer_whatsapp, customer_email optional, items array of product_id and quantity. Validates products exist and are available. Calculates total. Creates order and order_items. Generates order_ref. Calls monnify.create_payment_link(). Stores payment link on order. Returns order with payment link for customer to complete payment. If store has WhatsApp connected, sends notification to trader via whatsapp_client.send_text().

GET /orders — authenticated. All trader orders. Query params: status, date_from, date_to, limit, offset.

GET /orders/{order_ref} — authenticated. Single order with all items.

PATCH /orders/{order_ref}/status — authenticated. Update status to processing, delivered, cancelled. Sends WhatsApp notification to customer if their number was provided.

**monnify.py:**

get_access_token() — POST to Monnify auth endpoint with base64 encoded api_key:secret_key. Returns bearer token. Cache in Redis for 50 minutes (token expires in 60).

create_payment_link() — POST to Monnify initialize payment endpoint. Takes amount, order_ref as payment_ref, customer email if available, redirect URL. Returns checkout URL that customer uses to pay.

verify_payment() — GET to Monnify verify transaction endpoint with payment_ref. Returns transaction status and amount.

**Milestone:** Place a test order via public store page. Monnify payment link generated. Retrieve the link. Complete sandbox payment. Confirm order has payment_ref stored.

---

### Phase 4 — Monnify Webhook and Payment Confirmation

**webhook_monnify.py:**

POST /webhook/monnify — Monnify sends payment notifications here.

Validate Monnify webhook signature — Monnify uses a computed hash of the payload. Verify before processing anything.

Parse payload. Extract paymentReference (our order_ref), amountPaid, paid status.

Deduplication — check if monnify_ref already processed in transactions table. If yes return 200 immediately.

Find order by order_ref. If not found log and return 200.

If payment status is PAID and amountPaid matches order total_amount:

Update order payment_status to paid and status to processing.

Update wallet — increment available_balance by amountPaid minus platform fee. Increment total_earned. Increment total_orders_paid.

Log to transactions table — type order_payment, amount, fee, net_amount, monnify_ref.

Send WhatsApp notification to trader if connected. Message: "New order paid! Order {order_ref} — ₦{amount} received. Customer: {customer_name}. Reply 'orders' to see details."

Translate notification using llm.translate_message() before sending.

Return 200 immediately after processing.

**Platform fee logic:**

Free tier: 0% platform fee. All revenue goes to trader. AAJE revenue comes from subscriptions (future). During MVP we charge zero to maximize adoption.

This keeps our infrastructure simple — no complex fee splitting for MVP.

**Retry logic for failed webhook processing:**

If any step after signature validation fails, log the full error with the raw payload to a errors table or Supabase logs. Monnify retries webhooks automatically on non-200 responses. Return 200 only after successful processing. Return 500 if processing fails so Monnify retries.

**Milestone:** Complete a Monnify sandbox payment for a test order. Confirm webhook fires. Confirm order payment_status updated to paid. Confirm wallet balance incremented. Confirm WhatsApp notification received.

---

### Phase 5 — WhatsApp Agent and Command Center

**agent.py:**

build_context() — assembles trader state from database into a clean dict. Queries wallet, recent orders (last 5), today's revenue from transactions, product count, bizprint score. Applies pii_scrubber.scrub() before returning.

reason() — takes message string and context dict. Calls Llama 4 Scout with full context and agent_knowledge.md content in system prompt. 5 second timeout. Returns dict with response text, intent confirmed, tools to call, and language to use. On timeout or failure returns None and falls back to keyword routing.

The system prompt for reason() defines AAJE's character: direct, practical, knows Nigerian business context, never makes financial promises, only discusses financial and business topics, responds in the trader's language.

**onboarding_agent.py:**

handle_new_whatsapp_message() — when an unknown WhatsApp number messages AAJE. Checks if number is already linked to an account. If yes route normally. If no ask if they have an AAJE store. If yes send them to web to connect WhatsApp. If no send them the signup link at the storefront URL.

**order_agent.py:**

handle_my_orders() — loads pending and recent orders for the trader, formats as a numbered list showing order_ref, customer name, amount, status. Sends via WhatsApp.

handle_order_detail() — loads single order by ref, shows full breakdown with items, sends via WhatsApp.

**product_agent.py:**

handle_add_product() — uses LLM to extract product name and price from the trader's message. Example: "add ankara bag 3500" extracts name "Ankara Bag" and price 3500. Creates product. Confirms in WhatsApp: "Ankara Bag added at ₦3,500. Your store is updated."

handle_update_product() — similar extraction for updates.

**money_agent.py:**

handle_balance() — loads wallet, formats balance, sends. "Your wallet balance is ₦45,000. Total earned this month: ₦120,000."

handle_withdraw() — shows balance, asks amount, triggers WhatsApp Flow for PIN entry, on PIN success calls Monnify payout to trader's verified bank account, updates wallet, sends receipt.

handle_pay_supplier() — searches suppliers, shows match or collects new supplier, triggers PIN Flow, executes Monnify transfer, sends receipt.

**bizprint_agent.py:**

handle_bizprint() — loads latest bizprint, formats score and grade, generates one-sentence LLM insight, sends in trader's language.

**Navigation menu:**

When trader sends "/" or "menu" send a WhatsApp list message:

```
📦 My Orders
💰 My Balance
🏪 My Store Link
➕ Add Product
💸 Withdraw
👥 Pay Supplier
📊 My BizPrint
❓ Help
```

Each item selectable. Tapping routes to correct agent handler.

**Milestone:** WhatsApp connected to web account. Send "my orders" — see orders. Send "add bag ₦3500" — product appears on storefront. Send "my BizPrint" — score returned. Send "balance" — wallet shown. Send "menu" — navigation list appears. Send off-topic question — rail guard blocks it.

---

### Phase 6 — BizPrint Engine

**refinery.py:**

compute_bizprint() takes user_id and db session. Pulls all transactions from transactions table. Builds Pandas DataFrame. Computes four components.

Consistency score 0 to 25 — days with at least one paid order divided by total days on platform multiplied by 25.

Volume score 0 to 25 — average daily revenue divided by 50,000 naira benchmark multiplied by 25, capped at 25.

Growth score 0 to 25 — compare last 30 days revenue against previous 30 days. Positive growth maps to higher score. Flat maps to 12. Declining maps lower.

Tenure score 0 to 25 — days since account creation divided by 90 multiplied by 25, capped at 25.

Total score: sum of four components rounded to one decimal.

Credit grade mapping — 91+ is A+, 81-90 is A, 71-80 is B+, 61-70 is B, 51-60 is C+, 41-50 is C, below 41 is D.

Loan ceiling mapping — A+ maps to ₦500,000, A maps to ₦350,000, B+ maps to ₦200,000, B maps to ₦150,000, C+ maps to ₦75,000, C maps to ₦30,000, D maps to ₦0.

Upserts to bizprints table — one record per user, always the latest.

**scheduler.py:**

Weekly BizPrint job — every Sunday midnight compute_bizprint for all users with onboarding_complete True. After computation send WhatsApp summary if connected: "Your weekly BizPrint: Score {score}, Grade {grade}. {one-line LLM insight}."

Daily summary job — every evening at 8pm send traders their daily summary if they had any activity that day: "Today: {order_count} orders, ₦{revenue} received. Balance: ₦{balance}."

**bizprint.py routes:**

GET /bizprint/me — return latest bizprint record.
GET /bizprint/history — return last 12 computed bizprints for chart.

**intelligence.py route:**

GET /intelligence/economic-score/{user_id} — bearer token required. Returns anonymized BizPrint data. No PII.

**Milestone:** Process several test orders. Trigger compute_bizprint manually. Confirm score and grade computed correctly. Confirm history endpoint returns records. Call intelligence endpoint from Postman — confirm no PII in response.

---

### Phase 7 — Storefront Frontend

**store.html — Public store page:**

Reads slug from URL path. Fetches GET /store/{slug}. Displays store name, description, product grid. Each product card shows image, name, price, short description, "Order on WhatsApp" button. The button opens wa.me/{store_whatsapp_number} with a pre-filled message: "Hi, I want to order {product_name} at ₦{price}." If store has a checkout flow, show "Order Now" button that opens order form modal instead.

Order form modal — customer fills name, WhatsApp number, selects quantity. Submit calls POST /orders. On success shows payment link for Monnify checkout.

Theme is applied from store.theme_config — primary color, accent color, font — as CSS variables on the page root. This is the AI customization that makes each store feel unique.

**dashboard.html — Trader dashboard:**

Protected by JWT stored in localStorage. On load fetch GET /store/me/dashboard and GET /auth/me. Display store name, public link, wallet balance, pending orders count, today's revenue. Quick action buttons: View Orders, Add Product, Withdraw, My BizPrint. Recent orders table showing last 5.

**orders.html — Order management:**

Fetch GET /orders with status filter tabs: All, Pending, Paid, Processing, Delivered, Cancelled. Each row shows order_ref, customer name, amount, payment status, order status, date. Click row to see full order detail. Status update buttons per order.

**analytics.html — BizPrint and Revenue:**

Fetch GET /bizprint/me for current score. Fetch GET /bizprint/history for trend chart. Fetch transactions for revenue chart. Display: BizPrint score prominently with credit grade badge, four component scores as progress bars, weekly score history as line chart (Chart.js), monthly revenue bar chart, top products by order count, loan eligibility status and ceiling.

**connect.html — WhatsApp connection page:**

Simple page showing the steps: Enter WhatsApp number, receive OTP on WhatsApp, enter OTP to confirm. Calls POST /auth/connect-whatsapp then POST /auth/verify-whatsapp. On success redirects to dashboard with "WhatsApp connected" confirmation.

---

### Phase 8 — WhatsApp Flows

Build these six Flows using Meta's WhatsApp Flows builder. Each Flow has a data exchange endpoint on the backend.

**Flow 1 — PIN Setup**
Screen 1: masked 4-digit PIN field, confirm field, both must match before submit enabled. Backend endpoint: POST /flows/set-pin. Validates, hashes, stores. Returns success screen.

**Flow 2 — PIN Entry (Money Movement)**
Screen 1: transaction summary (what is about to happen), masked PIN field. Backend endpoint: POST /flows/verify-pin. Verifies PIN in real time. On success returns confirmation screen with transaction result. On failure returns error screen with remaining attempts. On lockout returns locked screen.

**Flow 3 — Withdrawal**
Screen 1: available balance shown, amount input with balance validation, destination bank name and account last 4 digits shown. Continue proceeds to PIN entry screen (PIN Flow embedded). Backend endpoint: POST /flows/withdraw. On PIN success executes Monnify payout, returns receipt screen.

**Flow 4 — Order Details**
Screen 1: full order breakdown — customer name, items list with quantities and prices, total amount, current status, date placed. Action buttons: Mark as Delivered, Cancel Order. Backend endpoint: POST /flows/update-order-status. Returns updated status screen. Follow-up message sent after: "Order {ref} marked as delivered."

**Flow 5 — BizPrint Details**
Screen 1: score displayed large with grade badge, four component score bars, loan eligibility and ceiling, AI-generated insight paragraph. No action needed — informational only. No follow-up message.

**Flow 6 — Account Balance**
Screen 1: available balance large and prominent, total earned this month, total orders paid, last 5 transactions listed. No action. No follow-up message.

---

### Phase 9 — Deployment

**Backend on Railway or Render:**

Push to GitHub main. Connect Railway to repo. Set build command: pip install -r requirements.txt. Set start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT. Add all environment variables. Deploy. Get HTTPS URL.

**Storefront on Vercel:**

Connect GitHub to Vercel. Set storefront/ as root directory. Deploy. Get HTTPS URL. Update FRONTEND_URL in backend environment variables.

**Configure webhooks:**

Meta webhook: backend URL at /webhook/whatsapp. Verify token from .env.
Monnify webhook: backend URL at /webhook/monnify. Set in Monnify dashboard.

**Confirm everything:**

Health endpoint returns 200. WhatsApp two-way confirmed on production URL. Monnify test payment confirmed on production URL. Store page loads correctly at Vercel URL.

---

### Phase 10 — Integration Testing

```
T1 — Web signup and AI store generation
     Sign up with email and business description
     Confirm AI extracts products correctly
     Confirm store live at public URL
     Confirm all products visible
     Confirm wallet at zero

T2 — Customer order and Monnify payment
     Visit public store URL
     Place order with customer details
     Confirm Monnify payment link generated
     Complete sandbox payment
     Confirm webhook fires on production URL
     Confirm order payment_status updated to paid
     Confirm wallet balance incremented
     Confirm WhatsApp notification sent to trader

T3 — WhatsApp connection
     Go to connect.html
     Enter WhatsApp number
     Receive OTP on WhatsApp
     Enter OTP on web
     Confirm whatsapp_verified True in database
     Send message from WhatsApp to AAJE
     Confirm routes to correct agent

T4 — WhatsApp order management
     Send "my orders" — confirm orders listed
     Send "menu" — confirm navigation list appears
     Tap "My Orders" from menu — confirm same result

T5 — Add product via WhatsApp
     Send "add ankara bag 3500"
     Confirm product created in database
     Visit public store URL
     Confirm ankara bag now visible

T6 — BizPrint computation
     Process at least 3 paid test orders
     Trigger compute_bizprint manually for test user
     Confirm score computed and stored
     Send "my BizPrint" via WhatsApp
     Confirm correct score and grade returned

T7 — PIN setup and withdrawal
     Set PIN via PIN Setup Flow
     Send "withdraw" via WhatsApp
     Open Withdrawal Flow
     Enter valid amount
     Enter correct PIN
     Confirm Monnify payout initiated
     Confirm wallet balance decremented

T8 — Rail guard
     Send "who won the Champions League"
     Confirm blocked with off-topic response
     Send "how does BizPrint affect my loan chances"
     Confirm this passes — it is financial

T9 — Agent reasoning
     Send "how far" after having 3 paid orders today
     Confirm agent responds with actual order count and revenue
     Confirm response contextual not templated
     Confirm response in trader's language
     Confirm response arrives under 5 seconds

T10 — Intelligence API
     Call GET /intelligence/economic-score/{user_id}
     With valid admin_token as bearer
     Confirm score and grade returned
     Confirm zero PII in response body

T11 — Full demo run
     Run complete 5-minute demo from web signup to BizPrint
     Time each minute
     Confirm under 5 minutes total
     No manual intervention needed
```

---

## The 5-Minute Demo Script

```
Minute 1 — Build the store
Open signup.html on screen
Type: "I sell ankara fabric ₦2,500 per yard,
ready-made dresses ₦8,000, head ties ₦1,500.
I also take custom orders."
Click Build My Store
AI generates store with 3 products
Show live link: aaje.store/adunola-fabrics

Minute 2 — Customer orders
Open store link on a second device (phone)
Customer taps "Order Now" on Ankara Fabric
Fills name and WhatsApp number
Monnify payment page opens
Complete sandbox payment
WhatsApp notification fires on trader's phone

Minute 3 — Trader manages on WhatsApp
Trader's phone shows: "New order paid — ₦2,500"
Trader replies "my orders"
AAJE shows the pending order
Trader taps Mark Delivered from Flow

Minute 4 — Add product from WhatsApp
Trader types "add lace fabric 4000"
AAJE confirms: "Lace Fabric added at ₦4,000"
Refresh store page — lace fabric now visible

Minute 5 — BizPrint identity
Trader types "my BizPrint"
AAJE returns score, grade, insight
Open analytics.html on laptop
Show score chart, revenue chart
Call GET /intelligence/economic-score from Postman
Show anonymized B+ grade returned in 200ms

Closing line:
"Before AAJE, Adunola managed her business
in her head and her orders in her DMs.
Now her store is live, her payments are tracked,
and her financial identity is being built
with every transaction.
One chat. One store. One identity. AAJE."
```

---

## Timeline to June First

```
Week 1 (Now)
  Phase 0 — All accounts and keys
  Phase 1 — Backend foundation
  Milestone: Two-way WhatsApp confirmed

Week 2
  Phase 2 — Auth and AI store generation
  Phase 3 — Products and orders
  Milestone: Store live, orders placed

Week 3
  Phase 4 — Monnify webhook and payment
  Phase 5 — WhatsApp agent and commands
  Milestone: Full payment flow confirmed
             WhatsApp managing orders

Week 4
  Phase 6 — BizPrint engine
  Phase 7 — Storefront frontend complete
  Milestone: Analytics page live
             BizPrint computing correctly

Week 5 (Final week before June 1)
  Phase 8 — WhatsApp Flows
  Phase 9 — Deployment
  Phase 10 — Integration testing
  Demo run — twice
  Milestone: Everything working on
             production URL
             Demo under 5 minutes
             clean every time
```

Start Phase 0 today. What do you need first?