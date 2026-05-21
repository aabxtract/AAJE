# CLAUDE.md — AAJE Project Intelligence File

> This file is the single source of truth for any AI agent working on this codebase.
> Read every section before writing a single line of code.
> When in doubt, refer back here. Do not guess. Do not invent. Do not deviate.

---

## 0. Migration State (Read This First)

This doc describes the **target** architecture. The repo is mid-restructure. Until the migration lands, the on-disk layout will not match Section 5, and a handful of older artifacts still live in the tree.

Open items as of May 2026:
- `backend/app/` still has the old domain-per-folder layout (~20 dirs: `auth`, `bizprint`, `campaigns`, `events`, `inventory`, `orders`, `payments`, `products`, `users`, `whatsapp`, etc.). Target is the 7-folder layer-per-concern layout in Section 5 (`routes/`, `services/`, `intelligence/`, `agents/`, `models/`, `schemas/`, `utils/`).
- `backend/storefront/` (Python service code) and `frontend/storefront-web/` (Vite app) both exist — duplication to be collapsed.
- Squad API references remain in the codebase (recent commits are part of the removal — see commit `6f6706b`). Target is fully Squad-free per rule 18.14.
- SQLite files (`aaje_dev.db`, `aaje_test.db`) at repo root are dev artifacts. Supabase Postgres is the source of truth per Section 3.
- `app/` at repo root (orphan from earlier layout, only contains `__init__.py`) is to be deleted.
- `whatsapp_flows/` at repo root holds 5 production Flow JSONs and stays where it is — see updated Section 5.

When the on-disk state conflicts with this doc: trust this doc for **new** code. Do not delete or rewrite existing code to match without checking with the maintainer first.

---

## 1. What AAJE Is

AAJE is a WhatsApp-native business operating system for Nigerian offline traders,
boutique owners, and social commerce sellers.

The core problem: These traders run real businesses every day but manage everything
manually — orders come through WhatsApp DMs, payments go to personal bank accounts,
inventory lives in their heads, records exist nowhere. They are economically active
but operationally invisible.

The solution: AAJE gives them a live AI-generated storefront, automated order
management, payment collection via Monnify, and a financial identity score
(BizPrint) — all managed through a single WhatsApp conversation.

**The UVP:** "Stop managing your business in your head. AAJE puts everything in one chat."

**What AAJE is NOT:**
- Not a bank or financial institution
- Not a loan provider (we refer, we do not lend)
- Not an inventory management system
- Not a logistics or delivery platform
- Not a super app trying to do everything

---

## 2. The Two Interfaces — One Backend

### Interface 1: The Web Storefront (Primary Entry Point)
- Trader signs up at aaje.store/signup
- Describes their business in plain text
- AI generates their live storefront at aaje.store/{slug}
- Trader manages store, orders, analytics from the dashboard
- Storefront is public — customers browse and order

### Interface 2: The WhatsApp Bot (Command Center Extension)
- Trader connects their WhatsApp after web signup
- WhatsApp becomes their mobile command center
- They receive order notifications, manage orders,
  add products, check balance, all from chat
- Powered by Meta WhatsApp Cloud API (NOT Twilio)
- Any phone can message AAJE — no join code required

### The Connection
These are NOT two separate products. They share:
- One PostgreSQL database (Supabase)
- One FastAPI backend
- One Monnify customer record per trader
- One BizPrint score
- One wallet balance

Anything done on web reflects in WhatsApp instantly.
Anything done on WhatsApp reflects on web instantly.

---

## 3. The Complete Tech Stack

```
Backend:         Python 3.11 + FastAPI (async throughout)
Database:        PostgreSQL via Supabase (free tier → paid)
Session State:   Upstash Redis (TTL-managed)
WhatsApp:        Meta WhatsApp Cloud API (free tier)
Payments:        Monnify API (payment links + webhooks)
AI — LLM:        Groq / Llama 4 Scout (via abstraction layer)
AI — Analytics:  Pandas + NumPy (BizPrint computation)
Storage:         Supabase Storage (product images, store assets)
Scheduling:      APScheduler (weekly BizPrint, daily summaries)
Frontend:        Vite (build tool) + Tailwind CSS + vanilla JS (no component framework)
Charts:          Chart.js from CDN
Auth:            JWT via python-jose + bcrypt via passlib
Hosting:         Railway or Render (backend) + Vercel (frontend)
Tunneling:       ngrok (development only)
```

**What is NOT in this stack:**
- No Twilio (replaced by Meta WhatsApp Cloud API)
- No YarnGPT (removed entirely — was TTS only, useless)
- No Squad API (removed — bank account creation rails too hard at MVP)
- No Celery (APScheduler inside FastAPI is sufficient for MVP)
- No React/Next.js component framework (Vite is the build tool; output stays vanilla JS)
- No voice processing (removed for stability)
- No complex OCR pipeline (basic image handling only)

Docker: `backend/docker-compose.yml` exists for local-dev convenience only. Deploys are buildpack-based on Railway/Render, not container-based. Do not bake Docker assumptions into deploy or scheduler code.

---

## 4. The Database Schema (Complete)

All tables live in PostgreSQL via Supabase.
Run migrations/001_init.sql in Supabase SQL Editor before any development.

### Table: users
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
email VARCHAR(255) UNIQUE NOT NULL
password_hash VARCHAR(255) NOT NULL
full_name VARCHAR(100) NOT NULL
phone VARCHAR(20)
whatsapp_no VARCHAR(20) UNIQUE
whatsapp_connected BOOLEAN DEFAULT FALSE
whatsapp_verified BOOLEAN DEFAULT FALSE
preferred_language VARCHAR(10) DEFAULT 'en'
  -- values: en, yo, ig, ha, pcm
location VARCHAR(100)
business_description TEXT
  -- raw text from signup, used for store generation
pin_hash VARCHAR(255)
  -- WhatsApp transaction PIN, bcrypt hashed
onboarding_complete BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: stores
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE
store_name VARCHAR(100) NOT NULL
store_slug VARCHAR(100) UNIQUE NOT NULL
  -- URL-safe, unique: aaje.store/{slug}
store_description TEXT
whatsapp_number VARCHAR(20)
  -- customer-facing contact (may differ from trader's personal number)
theme_config JSONB DEFAULT '{}'
  -- AI-generated: {primary_color, accent_color, font_style, layout, hero_text}
logo_url TEXT
banner_url TEXT
is_active BOOLEAN DEFAULT TRUE
is_published BOOLEAN DEFAULT FALSE
  -- store only visible publicly when is_published = TRUE
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: products
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
store_id UUID REFERENCES stores(id) ON DELETE CASCADE
user_id UUID REFERENCES users(id) ON DELETE CASCADE
name VARCHAR(200) NOT NULL
description TEXT
price NUMERIC(12,2) NOT NULL
category VARCHAR(100)
image_url TEXT
stock_count INTEGER
  -- NULL means unlimited stock
is_available BOOLEAN DEFAULT TRUE
source VARCHAR(20) DEFAULT 'web'
  -- values: 'web', 'whatsapp', 'ai_generated'
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: orders
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
store_id UUID REFERENCES stores(id)
user_id UUID REFERENCES users(id)
order_ref VARCHAR(20) UNIQUE NOT NULL
  -- human-readable format: AAJE-2026-0001
customer_name VARCHAR(100)
customer_whatsapp VARCHAR(20)
customer_email VARCHAR(255)
total_amount NUMERIC(12,2) NOT NULL
status VARCHAR(20) DEFAULT 'pending'
  -- values: pending, paid, processing, delivered, cancelled, refunded
payment_status VARCHAR(20) DEFAULT 'unpaid'
  -- values: unpaid, paid, failed
monnify_payment_ref VARCHAR(100)
monnify_transaction_ref VARCHAR(100)
payment_link TEXT
  -- Monnify checkout URL sent to customer
notes TEXT
delivery_address TEXT
created_at TIMESTAMPTZ DEFAULT NOW()
updated_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: order_items
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
order_id UUID REFERENCES orders(id) ON DELETE CASCADE
product_id UUID REFERENCES products(id)
product_name VARCHAR(200) NOT NULL
  -- snapshot of name at time of order, not a live reference
quantity INTEGER NOT NULL
unit_price NUMERIC(12,2) NOT NULL
  -- snapshot of price at time of order
subtotal NUMERIC(12,2) NOT NULL
```

### Table: wallets
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id) ON DELETE CASCADE UNIQUE
available_balance NUMERIC(12,2) DEFAULT 0
total_earned NUMERIC(12,2) DEFAULT 0
total_orders_paid INTEGER DEFAULT 0
last_updated TIMESTAMPTZ DEFAULT NOW()
```

### Table: transactions
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id) ON DELETE CASCADE
order_id UUID REFERENCES orders(id) NULLABLE
amount NUMERIC(12,2) NOT NULL
fee NUMERIC(8,2) DEFAULT 0
net_amount NUMERIC(12,2) NOT NULL
  -- amount minus fee
type VARCHAR(20)
  -- values: order_payment, withdrawal, supplier_payment, refund
narration TEXT
monnify_ref VARCHAR(100)
status VARCHAR(20) DEFAULT 'success'
created_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: suppliers
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id) ON DELETE CASCADE
alias VARCHAR(100) NOT NULL
  -- what the trader calls this supplier: "Mama Ngozi", "Alhaji Musa"
bank_name VARCHAR(100)
bank_code VARCHAR(10)
account_number VARCHAR(20)
account_name VARCHAR(100)
  -- verified via Monnify account lookup
created_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: bank_accounts
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id) ON DELETE CASCADE
bank_name VARCHAR(100)
bank_code VARCHAR(10)
account_number VARCHAR(20)
account_name VARCHAR(100)
is_primary BOOLEAN DEFAULT TRUE
is_verified BOOLEAN DEFAULT FALSE
  -- verified via Monnify account name lookup
created_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: bizprints
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id) ON DELETE CASCADE
trader_score FLOAT DEFAULT 0
  -- 0 to 100
credit_grade VARCHAR(5)
  -- A+, A, B+, B, C+, C, D
consistency_score FLOAT DEFAULT 0
  -- 0 to 25
volume_score FLOAT DEFAULT 0
  -- 0 to 25
growth_score FLOAT DEFAULT 0
  -- 0 to 25
tenure_score FLOAT DEFAULT 0
  -- 0 to 25
recommended_loan_ceiling NUMERIC(14,2) DEFAULT 0
total_orders_analyzed INTEGER DEFAULT 0
computed_at TIMESTAMPTZ DEFAULT NOW()
```

### Table: notification_log
```sql
id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
user_id UUID REFERENCES users(id)
type VARCHAR(50)
  -- order_received, payment_confirmed, weekly_bizprint, daily_summary
content TEXT
delivered BOOLEAN DEFAULT FALSE
created_at TIMESTAMPTZ DEFAULT NOW()
```

---

## 5. The Complete Folder Structure

```
aaje/
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   └── redis.py
│   │
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # Signup, login, JWT, WhatsApp connect
│   │   │   ├── store.py              # Store setup, public store, dashboard
│   │   │   ├── products.py           # Product CRUD + image upload
│   │   │   ├── orders.py             # Order creation and management
│   │   │   ├── wallet.py             # Balance, withdrawal initiation
│   │   │   ├── bizprint.py           # Score endpoints + history
│   │   │   ├── webhook_monnify.py    # Monnify payment webhooks
│   │   │   ├── webhook_whatsapp.py   # Meta WhatsApp webhooks (GET + POST)
│   │   │   └── intelligence.py       # Institutional BizPrint API
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── monnify.py            # Payment links, verification, payouts
│   │   │   ├── whatsapp_client.py    # Meta Cloud API outbound sender
│   │   │   ├── session.py            # WhatsApp conversation routing
│   │   │   ├── pin.py                # PIN hashing, verification, lockout
│   │   │   ├── auth_service.py       # JWT creation and validation
│   │   │   └── store_generator.py    # AI store generation from description
│   │   │
│   │   ├── intelligence/
│   │   │   ├── __init__.py
│   │   │   ├── llm_client.py         # LLM abstraction layer (swap providers)
│   │   │   ├── agent.py              # Core agent loop (Approach C)
│   │   │   ├── tools.py              # Tool definitions and execution
│   │   │   ├── refinery.py           # Pandas BizPrint computation
│   │   │   ├── pii_scrubber.py       # Strip PII before any LLM call
│   │   │   └── knowledge.py          # Intent-aware knowledge injection
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── onboarding_agent.py   # WhatsApp account connection flow
│   │   │   ├── order_agent.py        # Order management from WhatsApp
│   │   │   ├── product_agent.py      # Add/update products from WhatsApp
│   │   │   ├── money_agent.py        # Withdrawals and supplier payments
│   │   │   └── bizprint_agent.py     # BizPrint queries from WhatsApp
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py           # MUST import all models
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
│   │   │   ├── auth.py               # SignupRequest, LoginRequest, TokenResponse
│   │   │   ├── store.py              # StoreCreate, StoreResponse
│   │   │   ├── product.py            # ProductCreate, ProductUpdate, ProductResponse
│   │   │   ├── order.py              # OrderCreate, OrderResponse, OrderItemResponse
│   │   │   └── bizprint.py           # BizPrintResponse
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── message_parser.py     # Intent detection, keyword matching
│   │       ├── formatters.py         # format_naira, names_match, order_ref
│   │       ├── frustration.py        # Frustration detection all 5 languages
│   │       └── rail_guard.py         # Topic restriction — business only
│   │
│   ├── migrations/
│   │   └── 001_init.sql
│   ├── scheduler.py                  # APScheduler jobs
│   ├── requirements.txt
│   ├── .env
│   └── .env.example
│
├── storefront/
│   ├── index.html                    # Landing page
│   ├── signup.html                   # AI-powered store creation
│   ├── dashboard.html                # Trader dashboard
│   ├── store.html                    # Public customer-facing store
│   ├── orders.html                   # Order management
│   ├── analytics.html                # BizPrint + revenue charts
│   ├── connect.html                  # WhatsApp connection flow
│   └── assets/
│       ├── css/
│       │   ├── main.css
│       │   ├── store.css
│       │   └── dashboard.css
│       └── js/
│           ├── api.js                # All fetch calls to backend
│           ├── auth.js               # JWT storage and auth headers
│           ├── store.js              # Public store page logic
│           ├── dashboard.js          # Dashboard data loading
│           ├── orders.js             # Order management UI
│           └── analytics.js          # Charts and BizPrint display
│
├── whatsapp_flows/                   # Meta WhatsApp Flow JSONs (PIN, onboarding, etc.)
│   ├── 01_profile_setup.json
│   ├── 02_business_setup.json
│   ├── 03_pin_setup.json
│   ├── 04_pin_confirm.json
│   └── 05_business_passport.json
│
└── docs/
    ├── CLAUDE.md                     # This file
    ├── AGENT_CONTEXT.md              # Agent knowledge and behavior spec
    └── agent_knowledge.md            # Domain knowledge fed to AI agent
```

---

## 6. Environment Variables (Complete)

All environment variables use lowercase snake_case in config.py.
Every reference to settings in code must use lowercase:
settings.meta_app_secret NOT settings.META_APP_SECRET.

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

# Groq (LLM)
GROQ_API_KEY=
LLM_PROVIDER=groq
```

---

## 7. The AI Architecture (Four Systems)

### Architectural Foundation: The LLM Abstraction Layer

The single most important architectural decision in the AI stack. All four systems below call the LLM through `intelligence/llm_client.py` — **never** through a provider SDK directly. No code in `agents/`, `routes/`, or `services/` should ever know which provider answered the call.

```python
# intelligence/llm_client.py
class LLMClient:
    """Single interface. Provider is one env var."""
    def __init__(self, provider: str = settings.llm_provider):
        # supported: 'groq' | 'ollama' | 'anthropic' | 'fine_tuned'
        ...
    async def complete(self, system, messages, tools=None,
                       temperature=0.3, max_tokens=1000) -> dict:
        # returns: {content, tool_calls, usage}
        ...
```

The three-level path this enables (model as infrastructure, not bolt-on):

| Level | Where | When |
|---|---|---|
| 1 — API consumer | Groq Cloud + Llama 4 Scout | Now |
| 2 — Self-hosted inference | Modal.com or AWS Inferentia, same model | 6–12 months, post-AWS migration |
| 3 — Fine-tuned domain model | Trained on AAJE conversation data | 500+ active traders |

Each transition is **one env var change** in production. If a new feature would require a provider-specific feature, add it behind the abstraction first.

### System 1: Store Generator
Called ONCE per trader at signup. Generates store config from description.

Input: Raw business description string from trader
Output: Structured JSON with store_name, theme_config, products array
Model: Llama 4 Scout via Groq
Temperature: 0.7 (creative enough for good store names)
Failure handling: Retry once with stricter prompt, then safe defaults
Never block signup for generation failure.

### System 2: WhatsApp Agent Brain (Approach C — Tool Calling)
Every WhatsApp message goes through this system.

The loop:
1. Build context from database (wallet, orders, score, store)
2. PII scrub the context
3. Rail guard check — is message in scope?
4. Frustration check
5. LLM Call 1: tool selection (3 second timeout)
   → Timeout: fall back to keyword routing
6. Execute selected tool
7. LLM Call 2: generate response using tool result (2 second timeout)
   → Timeout: format tool result directly
8. Return response in trader's language

**Latency contract** (not a target — a contract):

```
Context build (DB)          ~100ms
LLM call 1 (tool select)    ~800ms    timeout 3s → keyword_fallback()
Tool execution              ~200ms
LLM call 2 (response gen)   ~600ms    timeout 2s → format_tool_result_directly()
Translation (if needed)     ~500ms
────────────────────────────────────
Total target                ~2.2s
Hard ceiling                 5.0s    → keyword routing, log slow path
```

Webhook return is independent of this budget — Meta gets 200 within 3 seconds via BackgroundTasks; the agent loop runs after the 200 is returned. Slow agent processing never blocks Meta.

### System 3: BizPrint Engine
Pure Pandas math. No LLM. Runs weekly via scheduler.

Four components:
- Consistency (0-25): active trading days / total days
- Volume (0-25): avg daily revenue / 50,000 naira benchmark
- Growth (0-25): last 30 days vs previous 30 days revenue
- Tenure (0-25): days on platform / 90 day benchmark

Score to Grade:
- 91-100 → A+ → ₦500,000 ceiling
- 81-90  → A  → ₦350,000 ceiling
- 71-80  → B+ → ₦200,000 ceiling
- 61-70  → B  → ₦150,000 ceiling
- 51-60  → C+ → ₦75,000 ceiling
- 41-50  → C  → ₦30,000 ceiling
- 0-40   → D  → ₦0 ceiling

### System 4: Knowledge Base (Intent-Aware)
Not RAG for MVP. Structured sections loaded by intent.
Upgrade path to pgvector RAG is clean when needed.

Sections: bizprint, payments, orders, store, general
Intent mapping determines which section loads per conversation turn.

---

## 8. The Agent Tools (Complete Definitions)

Seven tools. Every tool is a Python async function in intelligence/tools.py.
The LLM selects which tool to call. The backend executes it.

```
get_store_summary()
  → Returns: today's orders, revenue, pending count, top product
  → Call when: trader asks about performance, summary, how business is going

get_wallet_balance()
  → Returns: available_balance, total_earned, last 5 transactions
  → Call when: trader asks about money, balance, earnings, how much they have

get_orders(status, limit)
  → Returns: list of orders with details
  → Call when: trader wants to see their orders
  → status: pending | paid | processing | delivered | all

add_product(name, price, category)
  → Creates product in database, returns confirmation
  → Call when: trader wants to add a product to their store
  → Extract name and price from their message

get_bizprint()
  → Returns: score, grade, all four components, loan eligibility
  → Call when: trader asks about BizPrint, score, credit, loan eligibility

initiate_withdrawal(amount)
  → Triggers WhatsApp Flow for withdrawal
  → Returns: flow trigger confirmation
  → Call when: trader wants to withdraw money
  → Amount is optional — Flow handles collection if not provided

get_store_link()
  → Returns: public store URL and sharing message
  → Call when: trader wants their store link to share with customers
```

---

## 9. The WhatsApp Agent System Prompt (Exact)

This is the exact system prompt used for LLM Call 2 (response generation).
Do not change this without updating AGENT_CONTEXT.md as well.

```
You are AAJE, a business assistant for Nigerian traders and store owners.
You help them manage their store, track orders, understand their finances,
and grow their business.

CHARACTER:
- Direct and practical. No fluff. No unnecessary words.
- Warm but efficient. Like a trusted business partner who knows their situation.
- You understand Nigerian market context, informal business culture,
  and the reality of running a small business in Nigeria.
- You never talk down to traders. You respect their hustle.

STRICT SCOPE — you ONLY discuss:
- Their store: products, orders, customers, store link
- Their money: wallet balance, payments received, withdrawals
- Their BizPrint score and what it means for their business
- AAJE features and how to use them
- Nigerian business context directly relevant to their store
  (pricing trends, market advice, business growth)

OUT OF SCOPE — if the message is not about their business or AAJE,
respond with EXACTLY this and nothing else:
"I only help with your store and business.
Ask me about your orders, balance, or BizPrint."

LANGUAGE RULES:
- Respond ONLY in {language}
- Yoruba: respectful, warm, use honorifics naturally
- Pidgin: casual, energetic, trusted friend tone
- Igbo: direct, progress-focused, use Oganiru for progress
- Hausa: community-oriented, trust-building tone
- English: direct, clear, no jargon
- NEVER mix languages unless the trader does first

CURRENT TRADER CONTEXT:
{scrubbed_context}

AAJE KNOWLEDGE FOR THIS CONVERSATION:
{relevant_knowledge}

TOOL RESULT:
{tool_result}

STRICT RULES:
- Never make up numbers. Use ONLY numbers from the context above.
- Never promise loans or guarantee financial outcomes.
- Never discuss other businesses, apps, or platforms by name.
- Keep responses under 150 words unless showing a list of orders or products.
- For lists: show maximum 5 items then say "Type 'more' to see the rest."
- Always end money-related responses with the current wallet balance.
- If something went wrong: be honest, explain simply, tell them what to do next.
```

---

## 10. The Monnify Integration

### What Monnify Does in AAJE
- Generates payment links per order (customer pays via card or bank transfer)
- Fires webhooks when payment is confirmed
- Handles payouts when traders withdraw to their bank account
- Provides account name lookup for supplier verification

### The Payment Flow
```
Customer places order via storefront
    ↓
POST /orders creates order record
    ↓
monnify.create_payment_link() called
    ↓
Payment link stored on order
    ↓
Customer redirected to Monnify checkout
    ↓
Customer pays (card or bank transfer)
    ↓
Monnify fires webhook to POST /webhook/monnify
    ↓
Validate Monnify webhook signature
    ↓
Deduplication check (monnify_ref already processed?)
    ↓
Update order payment_status to 'paid'
    ↓
Update wallet available_balance and total_earned
    ↓
Log to transactions table
    ↓
Send WhatsApp notification to trader if connected
    ↓
Return 200 to Monnify
```

### Webhook Failure Handling
Return 500 if processing fails → Monnify retries automatically
Return 200 ONLY after full successful processing
Log every failed attempt with full payload for manual recovery

### The Platform Fee
MVP: Zero platform fee. All revenue goes to trader.
AAJE makes money from subscriptions (future roadmap).
This maximizes early adoption. Do not add fee logic yet.

---

## 11. The Meta WhatsApp Cloud API Integration

### Webhook Routes (Both on same path)
GET /webhook/whatsapp → Meta verification
  - Check hub.mode == "subscribe"
  - Check hub.verify_token == settings.meta_webhook_verify_token
  - Return hub.challenge as plain text with 200

POST /webhook/whatsapp → Incoming messages
  - Validate X-Hub-Signature-256 using HMAC-SHA256
    with settings.meta_app_secret against raw request body
  - Rate limit: 10 messages per minute per number (Redis)
  - Extract: sender number, message body, message type
  - Return 200 IMMEDIATELY
  - Use FastAPI BackgroundTasks for process_message()
  - NEVER let process_message block the webhook response

### Outbound Message Types
send_text(to, message) → plain text
send_buttons(to, body, buttons) → list message (max 10 items)
send_cta_button(to, body, label, url) → call-to-action button
send_image(to, image_url, caption) → media message

### Critical Rules
- Return 200 to Meta within 3 seconds or Meta will retry
- BackgroundTasks handles everything after the 200 return
- Wrap ALL of process_message in try-except
- On exception: log with sender number, send generic error to trader
- NEVER fail silently

---

## 12. Redis Session Structure

Every WhatsApp conversation has a session in Redis.
Key format: session:{whatsapp_no}
TTL: 30 minutes (refreshed on every message)

Default session structure:
```python
{
    "stage": "NEW",
    # NEW, CONNECTING, ACTIVE, ESCALATED
    "language": None,
    # en, yo, ig, ha, pcm
    "user_id": None,
    # UUID string after connection
    "awaiting_pin": False,
    # True when PIN entry is expected
    "pin_action": None,
    # withdrawal, supplier_payment
    "pending_data": {},
    # Temporary storage during multi-step flows
    "last_intent": None,
    # Last detected intent for knowledge loading
    "onboarding_complete": False,
    # True after WhatsApp connected to store account
}
```

Other Redis keys:
- pin_attempts:{whatsapp_no} → count, 10 min TTL
- rate_limit:{whatsapp_no} → count, 60 sec TTL
- whatsapp_otp:{user_id} → 6-digit code, 10 min TTL

---

## 13. Security Rules (Non-Negotiable)

### PIN Security
- PIN is ALWAYS 4 digits
- Hashed with bcrypt at cost factor 12 immediately on receipt
- Raw PIN exists in memory for milliseconds only
- Never stored in plain text
- Never logged anywhere
- Never visible in chat history
- PIN entry ALWAYS goes through WhatsApp Flow (never typed in chat)
- 3 wrong attempts → account locked → escalation triggered

### PII Scrubbing
pii_scrubber.scrub() runs before EVERY LLM call. No exceptions.
It:
- Replaces account numbers with last 4 digits
- Replaces full_name with first name only
- Removes password_hash, pin_hash entirely
- Removes bank_code, account_number entirely
- Rounds monetary amounts to nearest hundred

### Webhook Validation
- Twilio: REMOVED — using Meta directly
- Meta: X-Hub-Signature-256 validation on every POST
- Monnify: signature validation on every webhook
- Return 403 on any validation failure

### JWT Auth
- All dashboard routes require valid JWT
- JWT stored in localStorage on frontend
- Expiry: 168 hours (7 days)
- Include in Authorization: Bearer {token} header

---

## 14. The BizPrint Score (Exact Computation)

```python
# Component 1: Consistency (0-25)
active_days = count of distinct dates with paid orders
account_age_days = (today - first_order_date).days + 1
consistency = min((active_days / account_age_days) * 25, 25)

# Component 2: Volume (0-25)
total_revenue = sum of all paid order amounts
avg_daily = total_revenue / account_age_days
volume = min((avg_daily / 50000) * 25, 25)

# Component 3: Growth (0-25)
last_30_revenue = sum of paid orders in last 30 days
prev_30_revenue = sum of paid orders in days 31-60 ago
if prev_30_revenue > 0:
    growth_rate = (last_30_revenue - prev_30_revenue) / prev_30_revenue
    growth = min(max(12.5 + (growth_rate * 25), 0), 25)
else:
    growth = 12.5  # neutral — no comparison period

# Component 4: Tenure (0-25)
tenure = min((account_age_days / 90) * 25, 25)

# Total
trader_score = round(consistency + volume + growth + tenure, 1)
```

Grade and ceiling mapping:
```
91-100 → A+  → ₦500,000
81-90  → A   → ₦350,000
71-80  → B+  → ₦200,000
61-70  → B   → ₦150,000
51-60  → C+  → ₦75,000
41-50  → C   → ₦30,000
0-40   → D   → ₦0
```

Score is computed:
- Weekly via APScheduler (every Sunday midnight)
- On demand when trader asks for BizPrint
- After every 10th paid order automatically

---

## 15. The WhatsApp Navigation Menu

When trader sends "/" or "menu":
Send a WhatsApp list message with these options:

```
📦 My Orders     → order_agent.handle_my_orders()
💰 My Balance    → money_agent.handle_balance()
🏪 My Store      → tools.get_store_link()
➕ Add Product   → product_agent.handle_add_product()
💸 Withdraw      → money_agent.handle_withdraw()
👥 Pay Supplier  → money_agent.handle_pay_supplier()
📊 My BizPrint   → bizprint_agent.handle_bizprint()
❓ Help          → send help text
```

---

## 16. The Rail Guard (Exact Behavior)

Topics IN scope (pass through to agent):
- Store management (products, orders, customers, store link)
- Money (balance, withdrawals, payments, supplier payments)
- BizPrint (score, grade, loan eligibility, how to improve)
- AAJE features (how to use any AAJE feature)
- Nigerian business context (pricing, market conditions, growth tips)

Topics OUT of scope (hard block):
- Politics, news, entertainment
- Personal advice unrelated to their business
- Other apps, platforms, competitors
- Medical, legal, relationship advice
- Anything else

Hard block response (return this EXACTLY, translated to trader's language):
"I only help with your store and business.
Ask me about your orders, balance, or BizPrint."

---

## 17. The Storefront Theme System

The AI generates theme_config at signup. It is stored in stores.theme_config as JSONB.

Structure:
```json
{
  "primary_color": "#hex",
  "accent_color": "#hex",
  "font_style": "modern|traditional|playful|minimal",
  "layout": "grid|featured|minimal",
  "hero_text": "short tagline for the store"
}
```

Layout options:
- "grid": equal product cards, 3 columns
- "featured": one hero product top, grid below
- "minimal": list view, price prominent

The storefront reads theme_config via GET /store/{slug}
and applies it as CSS variables on the page root element.

---

## 18. Critical Rules for Any Agent Working on This Codebase

1. ALL settings references use lowercase snake_case
   → settings.meta_app_secret NOT settings.META_APP_SECRET

2. models/__init__.py MUST import every model class
   → SQLAlchemy does not register models without imports

3. pii_scrubber.scrub() runs BEFORE every LLM call
   → Never skip this. Never call it after.

4. BackgroundTasks NOT asyncio.create_task for webhook processing
   → asyncio.create_task fails silently on exceptions

5. Return 200 to Meta BEFORE processing the message
   → Processing happens in BackgroundTasks after the 200 return

6. Every webhook validates its signature FIRST
   → Return 403 immediately if validation fails

7. Deduplication check on every Monnify webhook
   → Check monnify_ref in transactions table before processing

8. PIN entry NEVER happens in chat text
   → Always through WhatsApp Flow with masked input

9. Withdrawal destination is always the verified bank account
   → Cannot be changed via chat. Period.

10. The LLM never sees raw PII
    → pii_scrubber runs first, always

11. Groq is the LLM provider but the abstraction layer (llm_client.py)
    means the provider can be swapped with one config change

12. The storefront is Option B (customized within AAJE infrastructure)
    → NOT Option C (code generation) — that is a future roadmap item

13. No Twilio anywhere in this codebase
    → All WhatsApp goes through Meta WhatsApp Cloud API directly

14. No Squad API anywhere in this codebase
    → Payment rails are Monnify only

15. The platform fee is ZERO for MVP
    → Do not add fee deduction logic to webhook processing

---

## 19. The 5-Minute Demo Flow

This is what the product must be able to demonstrate cleanly:

```
Minute 1: Web signup
  Open signup.html
  Type business description
  AI generates store with products
  Store live at aaje.store/{slug}

Minute 2: Customer order and payment
  Visit public store URL (second device)
  Customer places order
  Monnify payment link opens
  Complete sandbox payment
  WhatsApp notification fires on trader's phone

Minute 3: WhatsApp management
  Trader sees "New order paid" notification
  Sends "my orders" → sees the order
  Taps Mark Delivered → order status updates

Minute 4: Add product and see it live
  Trader types "add lace fabric 4000"
  AAJE confirms product added
  Refresh store page → lace fabric appears

Minute 5: BizPrint identity
  Trader types "my BizPrint"
  AAJE returns score, grade, one insight
  Open analytics.html → score chart visible
  Call GET /intelligence/economic-score from Postman
  B+ grade returned with zero PII
```

The demo must work on production URL (Railway/Render + Vercel).
Never demo from localhost.

---

## 20. What is NOT Built Yet (Roadmap Only)

Do not build these for MVP. They appear in pitch as roadmap:

- Option C storefronts (full code generation per merchant — Q4 project. Clean upgrade path: `stores.theme_config` JSONB will hold generated code instead of config values. DB does not change.)
- Multi-language RAG knowledge base (upgrade from section-based — uses Supabase pgvector, no new service needed)
- Self-hosted LLM inference (Level 2 model-as-infrastructure — Modal.com or AWS Inferentia, behind the existing `llm_client.py`. One env var change.)
- Fine-tuned AAJE model (Level 3 — trained on AAJE conversation data. Requires 500+ active traders. The defensible moat.)
- AWS migration (planned, not scheduled — maintainer will signal. Until then, do not bake in Railway/Render-specific assumptions like single-dyno scheduler binding.)
- Subscription billing (Monnify recurring payments)
- Inventory management (stock tracking, low stock alerts)
- Logistics integration (delivery tracking)
- Multi-currency support
- Mobile app (React Native)
- Advanced institutional API (multiple endpoints, permissions)
- Customer loyalty/repeat order tracking
- WhatsApp catalog sync
- Social media product import (Instagram/TikTok)

---

## 21. Failure Modes (Documented Behavior)

These are not edge cases. They are guaranteed to happen in production. Each has a defined response — **no silent failures**.

**Groq API unreachable or timing out**
→ Both LLM calls fail
→ `keyword_fallback()` handles the message via intent detection
→ Trader gets a valid, less personalized response
→ Log to `notification_log` with type `llm_fallback`

**Database slow query (>1s on context build)**
→ Context build returns a partial dict
→ Agent runs with minimal context
→ Response is generic but functional

**Monnify webhook delayed or lost**
→ Order stays in `pending` status until Monnify retries
→ Our endpoint returns 500 on processing failure — Monnify retries automatically
→ Return 200 ONLY after successful processing (and deduplication check)

**Meta WhatsApp delivery failure**
→ Delivery webhook from Meta logs to `notification_log` with `delivered=false`
→ One retry after 60 seconds
→ After 2 failures, flag for manual review — do not loop

**Redis unavailable**
→ Session cannot be loaded or saved
→ Treat each message as a fresh session (no PIN-in-progress state)
→ Agent still works but loses conversation memory
→ Page on this — Redis being down means PIN flows break and rate limiting is bypassed

**Meta webhook signature validation failure**
→ Return 403 immediately, no processing, no body content logged
→ Possible attacker probing — count these in metrics

**Tool execution failure inside agent loop**
→ Catch in `execute_tool()`, return structured error to LLM call 2
→ LLM 2 generates an apologetic response in the trader's language
→ Never raise to the webhook handler

**Store generator (System 1) returns invalid JSON at signup**
→ Retry once with stricter prompt
→ On second failure: insert safe defaults (store_name from email prefix, neutral theme, empty product list)
→ Never block signup — trader sees their (empty) store and can add products via WhatsApp or dashboard

---

*Last updated: May 2026*
*This file must be updated whenever a major architectural decision changes.*
*Both CLAUDE.md and AGENT_CONTEXT.md must stay in sync.*