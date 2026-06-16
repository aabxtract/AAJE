# fix.md — Path to MVP Demo

> Sequenced punch list to take the codebase from current state (May 2026,
> Twilio MVP pivot in progress) to a clean 5-minute demo run on production.
>
> **Order matters.** Each section unblocks the next. Don't skip ahead —
> step 5 cannot be tested until steps 1–4 work, etc.
>
> Pairs with `CLAUDE.md` (target architecture), `MVPsprint.md` (manual-
> transfer flow), and `AGENT_CONTEXT.md` (agent behavior). When this file
> conflicts with those, those win.

---

## Step 1 — Make the backend boot

**Why first:** nothing else can be tested if FastAPI won't start.

### 1.1 Pin missing runtime deps in `backend/requirements.txt`

Add:
```
groq                  # intelligence/llm_client.py imports AsyncGroq
pydantic[email]       # every auth schema uses EmailStr
python-jose[cryptography]  # services/auth_service.py JWT signing
```

**Done when:** `pip install -r requirements.txt && python -c "from app.main import app"` exits 0.

### 1.2 Verify `.env.example` covers what `main._validate_production_config()` checks

Confirm these are present (lowercase snake_case in code, uppercase in `.env`):
`JWT_SECRET`, `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`,
`TWILIO_WHATSAPP_FROM`, `FRONTEND_URL`, `DATABASE_URL`,
`UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `GROQ_API_KEY`.

**Done when:** booting with `APP_ENV=production` and an incomplete `.env`
fails fast with a readable list of missing keys.

---

## Step 2 — Fix the `whatsapp_verified` ghost field

**Why now:** `/auth/verify-whatsapp` writes `user.whatsapp_verified = True`
on a column that doesn't exist (`models/user.py` only has
`whatsapp_connected`). SQLAlchemy silently drops the attribute, so the
"verified" flag never persists. `UserResponse` also reads it and returns
`False` forever.

### Options (pick one)

**A. Add the column (recommended — matches CLAUDE.md §4):**
- `models/user.py`: add `whatsapp_verified = Column(Boolean, default=False)`
- The `add_missing_model_columns` lifespan hook in `main.py` will create
  it on next boot (already wired).

**B. Drop the concept:**
- Remove `whatsapp_verified` references from `routes/auth.py:117` and
  `schemas/auth.py:UserResponse`.
- `_find_linked_user` already keys off `whatsapp_connected`, so this
  doesn't break routing.

**Done when:** `verify-whatsapp` round-trip via curl returns
`{"whatsapp_verified": true, "whatsapp_connected": true}` (option A) or
the field is gone from the response shape entirely (option B).

---

## Step 3 — Finish the WhatsApp connect/verify flow on the React side

**Why now:** the React Onboarding/StoreSetup can request an OTP but has no
UI to enter the 6-digit code, and `lib/api.js:21` calls a non-existent
endpoint. Without this, no trader can link their WhatsApp — and without a
linked WhatsApp, nothing else in the demo works.

### 3.1 Fix `frontend/storefront-web/src/lib/api.js`

Replace:
```js
export const verifyWhatsappConnection = () => api.post('/auth/verify-whatsapp-connection')
```
with:
```js
export const verifyWhatsappConnection = ({ whatsapp_no, otp }) =>
  api.post('/auth/verify-whatsapp', { whatsapp_no, otp })
```

### 3.2 Add OTP entry UI

In `pages/admin/StoreSetup.jsx` (or `pages/Onboarding.jsx`, wherever the
trader first connects WhatsApp):
1. After clicking "Test Connection" / "Send Code", show a 6-digit input.
2. Submit `{ whatsapp_no, otp }` via the fixed `verifyWhatsappConnection`.
3. On success, persist `user` to `localStorage.aaje_user` (with
   `whatsapp_connected: true`).

**Done when:** signup → connect WhatsApp → receive OTP on phone → type it
back → user row shows `whatsapp_connected=true`. Inbound message from the
trader's number now routes through the agent loop (Step 1 of this sprint
already wired the lazy session hydration).

---

## Step 4 — Point the React app at the new endpoints

**Why now:** the React frontend is wired to the legacy `/api/storefront/*`
routes from the domain-per-folder layout. The new layer-per-concern
routers we've been building (`/store`, `/orders`, `/products`) aren't
called by the deployed UI. The customer storefront, dashboard, and order
management on web all break against the new backend.

### 4.1 Rewrite `lib/api.js`

Old → new endpoint map:
| Function | Old path | New path |
|----------|----------|----------|
| `createStore` | `POST /api/storefront/stores` | `POST /store/setup` |
| `getStoreBySlug` | `GET /api/storefront/stores/:slug` | `GET /store/:slug` |
| `updateStore` | `PUT /api/storefront/stores/:id` | `PATCH /store/me` |
| `createProduct` | `POST /api/storefront/products` | `POST /products` |
| `getProductsByStore` | `GET /api/storefront/products/:slug` | embedded in `GET /store/:slug` |
| `updateProduct` | `PUT /api/storefront/products/:id` | `PATCH /products/:id` |
| `deleteProduct` | `DELETE /api/storefront/products/:id` | `DELETE /products/:id` |
| `createOrder` | `POST /api/storefront/orders` | `POST /orders` |
| `getOrdersByStore` | `GET /api/storefront/orders/:storeId` | `GET /orders?...` (auth-scoped) |
| `updateOrderStatus` | `PUT /api/storefront/orders/:id/status` | `PATCH /orders/:order_ref/status` |

The new endpoints are auth-scoped via the JWT — `getOrdersByStore(storeId)`
collapses into `getOrders({ status, limit, offset })` since the backend
infers the store from the user.

### 4.2 Update payload shapes

- `createStore({ description })` → `POST /store/setup { business_description }`
- `OrderTable` reads `order.status` against the MVP statuses (see Step 5).

**Done when:** the React app's network tab shows it hitting `/store/...`,
`/orders/...`, `/products/...` — no more `/api/storefront/*`.

---

## Step 5 — Dashboard UI for the manual-transfer states

**Why now:** trader confirms/rejects from WhatsApp in the demo, but the
dashboard also needs to show transfer_claimed orders so the trader (and
the audience) can see the state transition on web.

### 5.1 `components/OrderTable.jsx` — status badges

Per `MVPsprint.md` §"Dashboard Visual Status":
```
⏳ pending           → grey
💸 transfer_claimed  → yellow (sort to top)
✅ confirmed         → green
❌ rejected          → red
📦 delivered         → blue
```

### 5.2 `pages/admin/Orders.jsx` — confirm/reject/deliver buttons

For each row:
- Status `transfer_claimed` → show `Confirm` and `Reject` buttons that
  `PATCH /orders/:order_ref/status` with `{ status: "confirmed" }` or
  `{ status: "rejected" }`.
- Status `confirmed` → show `Mark Delivered` button → `{ status: "delivered" }`.
- All buttons no-op (greyed) for other statuses.

### 5.3 Auto-refresh / sort

`transfer_claimed` rows pinned to the top; the rest by `created_at desc`.
Poll `/orders?limit=20` every 15s while the page is open (or wire SSE
later — not MVP).

**Done when:** a buyer-side claim shows up on the dashboard within 15s
without a manual refresh, and the trader can drive the same status
transitions from web that they drive from WhatsApp.

---

## Step 6 — Wire BizPrint to live data

**Why now:** `Dashboard.jsx` hard-codes the BizPrint score as `78`. The
agent's `get_bizprint` tool works, but the dashboard widget is fake.

### Changes
- Add `getBizprint` to `lib/api.js`: `GET /bizprint/me` (whichever route
  exposes the latest BizPrint — check `app/routes/intelligence_api.py`
  or wire a new one in `routes/bizprint.py`).
- `Dashboard.jsx` hero stat reads `bizprint.trader_score` and
  `bizprint.credit_grade` from the API response.
- Fallback: if BizPrint hasn't been computed yet (no paid orders), show
  `—` not `0`. The score should ONLY appear once the engine has data.

**Done when:** the hero strip on `/admin/dashboard` shows the same score
the agent returns when asked "my BizPrint".

---

## Step 7 — Local Twilio smoke test

**Why now:** every prior fix should be exercised under a real Twilio
webhook before claiming demo-ready.

### 7.1 Setup
- `ngrok http 8000` (or equivalent)
- Twilio sandbox → set inbound webhook to `https://<ngrok-id>.ngrok-free.app/webhook/whatsapp`
- `TWILIO_WEBHOOK_VALIDATE=true`, `APP_PUBLIC_URL=https://<ngrok-id>.ngrok-free.app`
- Trader's phone: `join {sandbox_code}` once

### 7.2 Run the demo flow once locally
1. Signup at `/signup` with a real email + the trader's real WhatsApp number
2. Generate store, set payout account on `/admin/store-setup` (with the
   disclosure copy now visible)
3. Connect WhatsApp → enter OTP → confirm `whatsapp_connected=true`
4. Visit `aaje.store/store/{slug}` from another device
5. Place an order with a buyer's WhatsApp number
6. Click "I've Transferred" → trader's phone vibrates within ~5s
7. Trader replies `confirm AAJE-XXXX` → bot acknowledges to trader only
8. Trader taps the wa.me link in the notification → personal WhatsApp
   opens to the buyer with the prefilled template
9. Trader replies `delivered AAJE-XXXX` → bot acknowledges
10. Trader replies `my BizPrint` → score returned

**Done when:** the round trip completes inside ~10s per step with no 500s
in the backend log and no Twilio signature failures.

---

## Step 8 — Production smoke test

**Why now:** Railway/Render quirks (cold starts, env wiring, CORS) don't
show up locally.

### Checks
- Deploy to Railway (or Render) with the production env vars set
- Vercel deploy of the React app pointing `VITE_API_URL` at the deployed
  backend
- Re-run the 10-step flow against the production URL pair
- Verify `notification_log` entries are written for every WhatsApp send
- Verify Twilio webhook validation passes against the production URL
  (the `APP_PUBLIC_URL` setting matters — Twilio signs the full URL,
  including any reverse-proxy hostname)

**Done when:** the production demo runs as smoothly as the local one,
including from a fresh trader account.

---

## Step 9 — Post-demo cleanup (parallelizable, not demo-blocking)

These are CLAUDE.md §0 open items. Run them only after the demo passes.

### 9.1 Squad removal
- Delete `services/squad_payment_service.py`
- Drop `users.squad_customer_id` (or leave the column dormant until next
  migration window — discuss with maintainer)
- Remove every `try: from app.payments.webhook import router as _squad_router`
  in `main.py`

### 9.2 Domain-per-folder → layer-per-concern migration
- The 20+ legacy folders (`auth/`, `bizprint/`, `campaigns/`, `events/`,
  `inventory/`, `orders/`, `payments/`, `products/`, `users/`,
  `whatsapp/`, etc.) need to fold into the 7-folder target layout in
  CLAUDE.md §5.
- Migrate one router at a time. Update `main.py`'s optional-router
  try/except blocks as each is collapsed.
- Avoid a big-bang rewrite — incremental + each commit boots.

### 9.3 Orphan paths
- Delete `app/` at repo root (only contains `__init__.py`)
- Delete dev SQLite files `aaje_dev.db`, `aaje_test.db` from version
  control (add to `.gitignore`)
- `whatsapp_flows/*.json` at repo root: keep inert during MVP, revisit
  when Meta migration lands (June 2026)

### 9.4 Storefront duplication
- `backend/storefront/` (Python service) vs `frontend/storefront-web/`
  (Vite app) need to collapse. The static `storefront/store.html` was
  wired to the new endpoints earlier — once the React storefront points
  at the new endpoints too (Step 4), pick one and delete the other.

---

## Step 10 — Doc sync

When the above lands:
- Update `CLAUDE.md` §0 (Migration State) to reflect what's now done.
- Update `MVPsprint.md` "What's NOT in MVP" if any deferred items shipped.
- Bump the "Last updated" footer in `CLAUDE.md` and `AGENT_CONTEXT.md`.
- Delete this `fix.md` once Steps 1–8 are green and Step 9 has a follow-up
  task tracked elsewhere.

---

## Quick reference — what's already done (this sprint)

For context, the immediate prior work (do NOT redo):
1. ✅ Lazy Redis session hydration from `users.whatsapp_no` on inbound
2. ✅ `PATCH /auth/me/payout-account` + React form + MVP disclosure copy
3. ✅ Agent tool definitions trimmed to 5 (add_product / initiate_withdrawal
   hidden from LLM, still dispatchable as deferred stubs)
4. ✅ `get_orders` status enum updated to MVP values
5. ✅ Knowledge sections rewritten to describe manual-transfer flow

Everything else in this file is still open.
