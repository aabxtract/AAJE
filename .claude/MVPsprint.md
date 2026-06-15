# MVP Sprint — Twilio WhatsApp + Manual Bank Transfer

> Pairs with CLAUDE.md and AGENT_CONTEXT.md. Describes the **MVP-only**
> flow. The Monnify-automated flow returns post-CAC; the Meta migration
> happens June 2026.

---

## The Order and Payment Flow (MVP)

```
Customer visits store
        ↓
Selects products
        ↓
Fills name AND WhatsApp number (required for the trader's deep link)
        ↓
Clicks "Place Order"
        ↓
Checkout screen appears showing:
  - Order summary (items + total)
  - Trader's bank account number
  - Trader's bank name
  - Account name
  - "Transfer ₦{amount} to this account"
        ↓
Customer makes the bank transfer manually
        ↓
Customer clicks "I've Transferred"
        ↓
PATCH /orders/{order_ref}/claim-transfer  (public, no auth)
        ↓
Order status → transfer_claimed
        ↓
Trader gets WhatsApp bot notification:
  - order ref, customer name, items, amount
  - "Check your {bank_name} account ending {last4}"
  - 💬 wa.me/{buyer_phone}?text={prefilled_template}   ← plain-text link
  - "Reply 'confirm AAJE-XXXX' to confirm or
     'reject AAJE-XXXX' if not received"
        ↓
Trader checks their bank app
        ↓
┌─────────────────────────────┐    ┌──────────────────────────────┐
│ Money is there:             │    │ Money is not there:          │
│ Trader replies              │    │ Trader replies               │
│ "confirm AAJE-0001"         │    │ "reject AAJE-0001"           │
│ → status = confirmed        │    │ → status = rejected          │
│ → bot replies to TRADER     │    │ → bot replies to TRADER      │
│   "Order confirmed"         │    │   "Order rejected"           │
│ → trader taps wa.me link    │    │ → trader taps wa.me link to  │
│   to tell buyer themselves  │    │   tell buyer themselves      │
└─────────────────────────────┘    └──────────────────────────────┘
```

**Critical:** the bot never messages the buyer. The wa.me deep link
inside the trader's notification is how the trader contacts the buyer
on their personal WhatsApp.

---

## Why Buyer-Side Bot Messages Are Removed

1. **Twilio sandbox friction:** Phase-1 buyers would need to send
   `join {sandbox_code}` before they could receive bot messages.
2. **Cost:** Twilio is per-message; halving outbound volume halves bot bill.
3. **24-hour session window:** Bot-to-buyer messages outside that window
   require approved templates. The trader's personal WhatsApp has no such
   constraint.
4. **The trader's personal touch matters:** "Hi Ngozi! Just confirmed your
   payment for AAJE-0001 — preparing your order now" lands better from the
   actual seller than from a bot.

The bot's job ends at delivering the trader the wa.me deep link. The
seller↔buyer chat is human-to-human.

---

## What Changes in the Database

Migration: `migrations/005_mvp_manual_transfer.sql`

```sql
-- Status values for orders (already supported via VARCHAR):
--   pending          → order placed, awaiting transfer
--   transfer_claimed → customer clicked "I've Transferred"
--   confirmed        → trader confirmed payment received
--   rejected         → trader did not receive transfer
--   delivered        → order fulfilled
--   cancelled        → order cancelled

-- No schema additions. The trader's payout account already lives on
-- users.verified_bank_account / verified_bank_code / verified_bank_name
-- (originally for Squad/Mono; repurposed for the manual-transfer MVP).
```

If the existing `users` columns prove inadequate (e.g. payment account
distinct from KYC account), add `users.bank_account_number`,
`users.bank_account_name`, `users.bank_name` — but for MVP we reuse the
existing `verified_*` columns.

---

## What Changes in the Frontend

### storefront/store.html — Three Modal Steps

**Step 1 — Order form:**
- Product summary, customer name, customer WhatsApp (required), email,
  quantity. Already implemented.

**Step 2 — Checkout (bank transfer instructions):**
- Order ref, bank, account number (with copy button), account name, amount,
  "I've Transferred" button. Already implemented.

**Step 3 — Claimed acknowledgement:**
- "We've notified {store_name} on WhatsApp. They'll confirm shortly.
  You'll hear back from them on WhatsApp directly." Already implemented.

The "I've Transferred" button calls:

```
PATCH /orders/{order_ref}/claim-transfer
```

No auth required. Public endpoint. Updates order status to
`transfer_claimed` and fires the trader's WhatsApp notification.

---

## What Changes in the Backend

### routes/orders.py — One New Endpoint

**PATCH /orders/{order_ref}/claim-transfer**
Public. No auth. Called when customer clicks "I've Transferred."

Behaviour:
- 404 if order missing
- 400 if status is not currently `pending`
- Idempotent on `transfer_claimed`: re-claiming is a no-op success
- Sets status to `transfer_claimed`
- BackgroundTasks the trader notification (does NOT block the response)

### services/whatsapp_client.py — Twilio rewrite

Replaces the current Meta-based client. Same function signatures so callers
don't change. Exposes:
- `send_text(to, message)`
- `send_cta_link(to, body, label, url)` — plain-text body with the URL
  appended; WhatsApp auto-linkifies. Upgrade path to Twilio Content
  templates with URL buttons after Phase 1.
- `send_image(to, image_url, caption)`

Phone numbers normalize to `whatsapp:+{e164}` before send.

### routes/webhook_whatsapp.py — Twilio rewrite

- Drop the GET verification endpoint (Meta-only).
- POST accepts `application/x-www-form-urlencoded`.
- Validate `X-Twilio-Signature` via `TwilioRequestValidator`.
- Extract `From`, `Body`, `MessageSid`.
- Return 200 with `Content-Type: text/xml`, body `<Response/>`.
- BackgroundTasks dispatches the message to the session router.

### services/session.py — Direct command shortcut

Before falling through to the LLM agent loop, match these in order:

```python
COMMAND_PATTERNS = [
    (r"^confirm\s+(AAJE-\d+)\s*$",    handle_confirm),
    (r"^reject\s+(AAJE-\d+)\s*$",     handle_reject),
    (r"^delivered\s+(AAJE-\d+)\s*$",  handle_delivered),
    (r"^orders\s*$",                  handle_list_orders),
    (r"^balance\s*$",                 handle_balance),
    (r"^menu\s*$|^/menu\s*$|^/$",     handle_menu),
]
```

Direct command handlers reply to the trader ONLY. No buyer-side WhatsApp
sends.

---

## The Trader Notification Template

The bot sends ONE message to the trader when a transfer is claimed:

```
💸 New transfer claim — AAJE-0001

Customer: Ngozi
Amount: ₦8,500
Items: 2× Lace Fabric

Check your GTBank account ending 6789 for the transfer.

💬 Message Ngozi: https://wa.me/2348012345678?text=Hi%20Ngozi%21%20This%20is%20Adunola%27s%20Boutique...

When you've checked:
✅ Reply "confirm AAJE-0001" if received
❌ Reply "reject AAJE-0001" if not received
```

The wa.me URL is built server-side with:
- buyer phone normalized to E.164 digits (no `+`, no `whatsapp:`)
- pre-filled message URL-encoded, includes store name + order ref + items

---

## The wa.me Deep-Link Template

```
Hi {buyer_first_name}! This is {store_name}.

We've confirmed your payment for order {order_ref}:
{items_summary}
──────
Total: ₦{amount}

When would you like to receive your order?
```

URL-encoded and appended as `?text=...` to `https://wa.me/{phone}`.

The trader sends/edits this from their PERSONAL WhatsApp — the AAJE bot
has no role in this chat.

---

## The Six WhatsApp Commands

```
orders                — see latest 5 orders, transfer-claimed first
confirm AAJE-XXXX     — confirm payment received (transfer_claimed → confirmed)
reject AAJE-XXXX      — payment not received   (transfer_claimed → rejected)
delivered AAJE-XXXX   — mark order fulfilled    (confirmed → delivered)
balance               — confirmed sales this month
menu                  — see this list
```

All deterministic, no LLM call required.

---

## Order Status Transitions

```
pending
  ↓ customer clicks "I've Transferred" → PATCH /orders/{ref}/claim-transfer
transfer_claimed
  ↓ trader replies "confirm AAJE-X"        ↓ trader replies "reject AAJE-X"
confirmed                                   rejected
  ↓ trader fulfils order                    (trader follows up with buyer
  ↓ trader replies "delivered AAJE-X"        via wa.me link manually)
delivered
```

`confirmed → rejected` is NOT a legal transition (you can't un-confirm).
Stuck orders are corrected via the dashboard.

---

## Dashboard Visual Status

```
⏳ Pending           → grey badge
💸 Transfer Claimed  → yellow badge — needs trader attention
✅ Confirmed         → green badge
❌ Rejected          → red badge
📦 Delivered         → blue badge
```

`transfer_claimed` orders sort to the top automatically. The trader can
confirm/reject/deliver from the dashboard or from WhatsApp — both paths
hit the same status-update logic.

---

## Onboarding Disclosure (Mandatory)

When a trader signs up and adds their bank account details, surface this
clearly on the form:

> Your account number will be shown to customers at checkout. Make sure
> this is the account you want to receive payments on. When AAJE
> integrates Monnify next month, this becomes automated — for now it's
> manual and transparent.

This sets correct expectations and avoids the "my personal account is
publicly visible" surprise.

---

## Twilio Phase Roadmap

| Phase | Channel | When | What's gated |
|-------|---------|------|--------------|
| 1 | Twilio sandbox | now | trader + dev numbers must `join {sandbox_code}` |
| 2 | Twilio production WhatsApp | after MVP smoke test passes | requires Twilio Business + WhatsApp Sender approval |
| 3 | Meta WhatsApp Cloud API | June 2026 | post-validation; restores in-chat Flows, removes join-code, lowers cost |

The `services/whatsapp_client.py` abstraction is what makes phase 3 a
one-file swap.

---

## What's NOT in MVP

- ❌ Bot-initiated buyer messages (confirmed/rejected) — replaced by trader's
  wa.me deep link
- ❌ Monnify payment links — deferred to post-CAC
- ❌ PIN flow + withdrawals + supplier payments — gated on Monnify
- ❌ Add-product from chat — dashboard only for MVP
- ❌ Interactive list menus — text-only for MVP (template approval friction)
- ❌ Meta WhatsApp Flows — replaced by Twilio sandbox/production

These all return on their own scheduled rails. None are forgotten.
