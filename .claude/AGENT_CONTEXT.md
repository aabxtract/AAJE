# AGENT_CONTEXT.md — AAJE WhatsApp Agent Specification

> Operational spec for the WhatsApp agent. This file pairs with CLAUDE.md:
> CLAUDE.md is the codebase-wide source of truth; AGENT_CONTEXT.md is the
> agent's behavior contract. Anything that affects how the agent reasons,
> responds, or executes tools belongs here.
>
> **Sync rule:** §9 of CLAUDE.md (the system prompt) is mirrored verbatim in
> this file. Any change to that prompt MUST land in both files in the same
> commit, or the agent will drift from documented behavior.

---

## 0. Scope of This Document

This file covers:
- The agent's role within AAJE
- The agent loop (Approach C — structured tool calling)
- The exact system prompt
- Tool definitions and selection rules
- Rail guard behavior
- Session state contract
- Language rules across en/yo/ig/ha/pcm
- PII handling
- Failure modes specific to the agent
- Knowledge injection model

This file does NOT cover: web routes, storefront generation, Monnify
integration, BizPrint computation, or database schema. For those, see CLAUDE.md.

---

## 1. The Agent's Role

The WhatsApp agent is the trader-facing brain of AAJE on WhatsApp. It is one
of four AI systems (CLAUDE.md §7) but the only one a trader interacts with
directly day-to-day.

**MVP channel:** Twilio WhatsApp (sandbox in Phase 1, production in Phase 2,
Meta migration June 2026). The agent code is identical across phases —
provider swaps live in `services/whatsapp_client.py` only.

**Bot direction is one-way:** bot → trader only. The bot never messages a
buyer. Trader-to-buyer follow-up happens on the trader's personal WhatsApp
via a `wa.me` deep link embedded in the trader's notification (§11 of
CLAUDE.md).

It exists to:
- Answer questions about the trader's store, money, and BizPrint
- Execute actions on the trader's behalf (view orders, get store link) via
  tool calls
- Receive direct commands: `confirm AAJE-X`, `reject AAJE-X`,
  `delivered AAJE-X` to update order status
- Respect the trader's language and Nigerian business context
- Stay strictly in scope — refuse off-topic conversation politely

It does NOT (for MVP):
- Move money — there is no withdrawal flow until Monnify re-enables post-CAC
- Accept PIN entry — deferred with withdrawals
- Send messages to buyers — bot direction is one-way
- Add products from chat — deferred to dashboard for MVP
- Promise loans, predict approvals, or quote outside the BizPrint ceiling
- Discuss competitors, news, politics, personal life, medical, legal advice
- Mix languages unless the trader does first
- Invent numbers — every figure comes from the tool result or trader context

---

## 2. The Agent Loop (Approach C — Tool Calling)

Every inbound WhatsApp message routes through this loop. The loop runs in
`BackgroundTasks` AFTER the webhook has returned 200 (empty TwiML) to
Twilio (CLAUDE.md §11).

### Direct command shortcut (bypasses LLM)

Before the agent loop runs, the session router checks for direct commands.
These execute deterministically without an LLM call:

```
confirm AAJE-XXXX    → mark order confirmed   (only if status=transfer_claimed)
reject AAJE-XXXX     → mark order rejected    (only if status=transfer_claimed)
delivered AAJE-XXXX  → mark order delivered   (only if status=confirmed)
orders               → list latest 5 orders
balance              → wallet snapshot
menu                 → text help
```

All command handlers reply to the trader on WhatsApp. **None send messages
to the buyer.** Trader-to-buyer follow-up is the wa.me deep link inside the
original transfer-claimed notification.

If no direct command matches, fall through to the LLM agent loop:

```
inbound message
   ↓
1. Load Redis session (key: session:{whatsapp_no})
   ↓
2. Check connection: NEW or no user_id → onboarding response, exit
   ↓
3. Build trader context from DB
   - wallet (available_balance, total_earned)
   - recent orders (last 5)
   - today_revenue from transactions
   - product_count
   - latest BizPrint (score, grade)
   ↓
4. pii_scrubber.scrub(context)   ← MANDATORY (CLAUDE.md §13, §18 rule 3)
   ↓
5. Rail guard check
   - is_in_scope(message)? if false: send off-topic response, exit
   ↓
6. Frustration check
   - detect_frustration(message)? if true: escalation path, exit
   ↓
7. LLM Call 1: tool selection
   - 3s timeout
   - on timeout: keyword_fallback() routes to keyword-matched intent
   ↓
8. Execute selected tool (intelligence/tools.py)
   - 200ms target
   - on failure: structured error result, NOT a raise
   ↓
9. LLM Call 2: response generation using tool result
   - 2s timeout
   - on timeout: format_tool_result_directly()
   ↓
10. Translate to trader.preferred_language if not English
   ↓
11. whatsapp_client.send_text(to=sender, body=response)
   ↓
12. Persist last_intent on session
```

### Latency contract (not a target — a contract)

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

Webhook return to Twilio is independent of this budget. Twilio gets 200
(empty TwiML) within 5 seconds via BackgroundTasks; the agent loop runs
after the 200 is sent. **Slow agent processing never blocks Twilio.**

### LLM provider abstraction

All LLM calls go through `intelligence/llm_client.py` (`LLMClient.complete()`).
The agent code never imports `groq`, `anthropic`, or any provider SDK directly.
Provider is selected by `settings.llm_provider` — one env var change to swap
from Groq → self-hosted Modal → fine-tuned. See CLAUDE.md §7 for the three-
level model-as-infrastructure path.

### WhatsApp provider abstraction

`services/whatsapp_client.py` exposes a stable surface: `send_text`,
`send_cta_link`, `send_image`. The agent does NOT know whether the
underlying provider is Twilio or Meta. The June 2026 Meta migration swaps
this single file; agent code is unchanged.

---

## 3. The System Prompt (Exact)

This is the prompt used for **LLM Call 2** (response generation). It is
identical to CLAUDE.md §9 — both files must update together.

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

### LLM Call 1 (tool selection) prompt

LLM Call 1 uses a separate, terser system prompt focused on tool routing. It
is provided the user message + a list of available tools (CLAUDE.md §8) and
returns either a single tool name with arguments, or `none` (meaning the
response should come from LLM Call 2 alone without a tool result).

Temperature for tool selection: **0.0**. Determinism matters more than
creativity here.

---

## 4. The Tools (5 for MVP)

Defined in `intelligence/tools.py`. Each is a Python async function. The LLM
selects which to call; the backend executes. Tool result is structured JSON,
not free text.

`add_product` and `initiate_withdrawal` are **deferred** for MVP. Products
are added via the dashboard; withdrawals require Monnify (post-CAC).

| Tool | Args | Returns |
|------|------|---------|
| `get_store_summary()` | — | today's orders, today_revenue, pending count, top product |
| `get_wallet_balance()` | — | available_balance, total_earned, last 5 transactions |
| `get_orders(status, limit)` | status: pending\|transfer_claimed\|confirmed\|rejected\|delivered\|all; limit: int | list of orders |
| `get_bizprint()` | — | score, grade, 4 components, loan ceiling |
| `get_store_link()` | — | public URL, share message |

### Tool selection guidance for LLM Call 1

- Trader asks about **money, balance, earnings** → `get_wallet_balance`
- Trader asks about **performance, summary, how business is going** → `get_store_summary`
- Trader wants **to see orders** → `get_orders` (default status="all", limit=5)
- Trader asks about **BizPrint, score, credit, loan eligibility** → `get_bizprint`
- Trader wants their **store link** → `get_store_link`
- Trader sends greeting, vague question, or general business advice → no tool, response from prompt alone
- Trader sends `confirm AAJE-X` / `reject AAJE-X` / `delivered AAJE-X` →
  handled by the direct-command shortcut (§2) **before** the LLM loop runs

### Tool execution rules

- All MVP tools are async and read-only. No state-changing tool is exposed
  to the LLM in MVP — status changes go through deterministic direct commands.
- Tool failures return a structured error dict — never raise out of the loop.
  LLM Call 2 generates an apologetic response in the trader's language.

---

## 5. Rail Guard

`utils/rail_guard.is_in_scope(message)` runs BEFORE LLM Call 1. If it returns
False, the agent sends the hard-block response without invoking the LLM.

**In scope:** store management, money, BizPrint, AAJE features, Nigerian
business context directly relevant to the trader.

**Out of scope:** politics, news, entertainment, personal advice, other
apps/platforms by name, medical, legal, relationship advice, anything else.

**Hard-block response** (translated to trader's language):

```
I only help with your store and business.
Ask me about your orders, balance, or BizPrint.
```

The rail guard is **belt-and-braces**: even if it lets a message through, the
system prompt (§3) instructs the LLM to refuse off-topic discussion with the
same exact message. Both layers must agree.

---

## 6. Session State Contract

Every conversation has a Redis session. Key: `session:{whatsapp_no}`.
TTL: 30 minutes, refreshed on every message.

```python
{
    "stage": "NEW",
    # NEW, CONNECTING, ACTIVE, ESCALATED
    "language": None,
    # en, yo, ig, ha, pcm
    "user_id": None,
    # UUID string after WhatsApp linked to account
    "pending_data": {},
    # Temporary storage during multi-step flows
    "last_intent": None,
    # Last detected intent — drives knowledge injection on next turn
    "onboarding_complete": False,
}
```

`awaiting_pin`, `pin_action`, and the `LOCKED` stage are **omitted in MVP**
because there is no PIN flow. They return alongside withdrawals post-CAC.

### Stages

| Stage | Meaning | Agent behavior |
|-------|---------|---------------|
| `NEW` | No session or no user_id | Send sandbox "join code" guidance + "Connect AAJE" link, exit |
| `CONNECTING` | OTP sent, awaiting verification | Accept OTP, transition to ACTIVE |
| `ACTIVE` | Linked and operational | Direct-command check → fall through to full agent loop |
| `ESCALATED` | Frustration detected | Defer to human / send help message |

### Other Redis keys

- `rate_limit:{whatsapp_no}` — count, 60-sec TTL (5 msg/min ceiling)
- `whatsapp_otp:{user_id}:{whatsapp_no}` — 6-digit OTP, 10-min TTL

`pin_attempts:{whatsapp_no}` is **not used** in MVP.

---

## 7. Language Rules

The agent supports 5 languages. The trader's `preferred_language` on the
`users` row is the source of truth.

| Code | Language | Tone |
|------|----------|------|
| `en` | English | Direct, clear, no jargon |
| `yo` | Yoruba | Respectful, warm, honorifics |
| `pcm` | Nigerian Pidgin | Casual, energetic, trusted friend |
| `ig` | Igbo | Direct, progress-focused (use *Oganiru* for progress) |
| `ha` | Hausa | Community-oriented, trust-building |

### Translation policy

- LLM Call 2 generates in the trader's language directly when possible — this
  is preferred over translating English output.
- For deterministic system messages (PIN prompts, error replies), use static
  translation tables — never round-trip through the LLM.
- **Never mix languages** unless the trader has done so first.
- If detection is uncertain, default to English.

---

## 8. PII & Security Rules

### PII Scrubbing (CLAUDE.md §13)

`pii_scrubber.scrub()` runs BEFORE every LLM call. No exceptions. It:

- Replaces account numbers with last 4 digits
- Replaces `full_name` with first name only
- Removes `password_hash`, `pin_hash` entirely
- Removes `bank_code`, full `account_number` entirely
- Rounds monetary amounts to nearest hundred

The LLM never sees raw PII. If a tool result contains sensitive fields,
they are stripped before being injected into the LLM Call 2 prompt.

### PIN Security (deferred — see CLAUDE.md §13)

MVP has no PIN flow. The rules below apply when PIN returns alongside
withdrawals post-CAC:

- PIN is ALWAYS 4 digits, bcrypt cost 12
- Raw PIN exists in memory for milliseconds only
- Never logged, never visible in chat history
- **PIN entry under Twilio:** hosted web form over HTTPS (no native masked
  input in Twilio chat). The bot sends a one-tap link.
- **PIN entry under Meta (post-June migration):** WhatsApp Flow with masked
  input. NEVER typed in chat.
- 3 wrong attempts → session.stage = `LOCKED` → escalation triggered

The agent must REFUSE to accept a PIN typed into chat under any condition,
even if a trader sends one unprompted.

### Withdrawal destination (deferred)

When withdrawals re-enable, the destination is always the trader's verified
bank account on record. It CANNOT be changed via chat. The agent must
refuse if a trader tries to redirect a withdrawal to a different account.

### Logging

- Never log the message body of an inbound webhook
- Never log PIN attempts, even failures (when PIN returns)
- Sender WhatsApp number can be logged for rate-limit/abuse tracking, but
  prefer last-4-digit masking when written to long-lived logs

---

## 9. Failure Modes (Agent-Specific)

See CLAUDE.md §21 for the full failure mode catalog. The ones the agent
specifically handles:

| Failure | Agent response |
|---------|---------------|
| **Groq API unreachable or timeout (LLM Call 1)** | `keyword_fallback()` routes by intent keywords; tool still executes if matched; LLM Call 2 also fails → format tool result directly |
| **LLM Call 2 timeout** | `format_tool_result_directly()` renders the tool result without LLM polish; trader gets a valid, less personalized response |
| **Tool execution failure** | Catch in `execute_tool()`, return structured error dict to LLM Call 2; LLM 2 generates an apologetic response in the trader's language; NEVER raise out to the webhook handler |
| **Context build slow (>1s)** | Return partial context dict; agent runs with minimal context; response is generic but functional |
| **Redis unavailable** | Treat each message as a fresh session; agent still works but loses conversation memory; **page on this** — Redis being down means rate limiting is bypassed |
| **Off-topic message slips past rail guard** | System prompt (§3) instructs LLM to refuse with the standard message; defense in depth |
| **Trader sends a 4-digit string** | Treat as normal text. MVP has no PIN flow, so digits are never auth tokens. When PIN returns post-MVP, the agent must NOT interpret chat-typed digits as a PIN. |

Every fallback path **must log to `notification_log`** with type `llm_fallback`
or `tool_failure` so degradation is observable.

---

## 10. Knowledge Injection (Intent-Aware)

Not RAG for MVP. The knowledge base is a set of structured sections in
`intelligence/knowledge.py`, loaded by intent.

### Sections

| Section | Loaded when intent matches |
|---------|--------------------------|
| `bizprint` | bizprint, score, credit, loan |
| `payments` | balance, withdraw, pay, money |
| `orders` | orders, sales, customer |
| `store` | store, link, product, share |
| `general` | greeting, help, unknown |

### Injection mechanism

The matched section's content is inserted into the `{relevant_knowledge}` slot
of the system prompt (§3). Sections are short (under 500 chars each) so the
prompt stays inside the token budget.

### Upgrade path

When trader population justifies it (CLAUDE.md §20), this becomes pgvector RAG
inside Supabase. No new service needed. The interface from agent → knowledge
stays a single string return; only the backing implementation changes.

---

## 11. Navigation Menu (CLAUDE.md §15)

MVP is text-only. When trader sends `menu`, send the following plain-text
message (no interactive list — Twilio sandbox + template-approval friction
avoided for MVP):

```
AAJE commands

📦 orders              — see your latest orders
✅ confirm AAJE-XXXX   — confirm a transfer-claimed order is paid
❌ reject AAJE-XXXX    — payment not received
📬 delivered AAJE-XXXX — mark a confirmed order as delivered
💰 balance             — total confirmed sales this month
❓ menu                — this list
```

Direct commands bypass the LLM entirely — they route through the §2
direct-command shortcut to deterministic handlers. This saves LLM calls on
the most common actions and guarantees demo-flow determinism.

Interactive list menus, add-product-from-chat, withdrawal, and supplier
payment all return when Meta migration lands (June 2026) and/or Monnify
re-enables.

---

## 12. Sub-Agents (per domain)

Defined in `app/agents/`. Each is a thin Python module — not a separate LLM
agent. They group tool calls + formatting logic for a specific domain.

MVP scope below. `money_agent.handle_withdraw`, `product_agent.handle_add_product`,
and supplier-payment paths are deferred.

| Module | Responsibility |
|--------|---------------|
| `onboarding_agent.py` | Handle unknown WhatsApp numbers; route new vs. linked traders; surface Twilio sandbox join-code guidance during Phase 1 |
| `order_agent.py` | List orders, show single order detail, execute confirm/reject/delivered status changes |
| `money_agent.py` | Wallet balance display (withdrawal flow trigger deferred) |
| `bizprint_agent.py` | Format BizPrint score + grade + 1-sentence LLM insight |

The main agent loop (§2) decides which sub-agent to dispatch to based on
the tool selected by LLM Call 1, or directly on a recognized command.
Sub-agents do NOT make their own LLM calls except for `bizprint_agent`
(1-sentence insight generation). All LLM access still flows through
`intelligence/llm_client.py`.

---

## 13. Critical Don'ts

Quick reference. Every item maps to a rule in CLAUDE.md §13 or §18.

- ❌ **Never** call a provider SDK (`groq`, `anthropic`, `twilio`) directly.
  Use `LLMClient` / `whatsapp_client`.
- ❌ **Never** message a buyer from the bot. Trader-to-buyer follow-up uses
  the wa.me deep link from the trader's notification (CLAUDE.md §11).
- ❌ **Never** skip `pii_scrubber.scrub()` before an LLM call.
- ❌ **Never** accept a PIN typed in chat (when PIN returns post-MVP).
- ❌ **Never** redirect a withdrawal to a different bank account from chat
  (when withdrawals return).
- ❌ **Never** invent numbers, prices, balances, or order counts. Use only
  what the tool result or context contains.
- ❌ **Never** promise loans, guarantee approvals, or quote a loan ceiling
  above what BizPrint computed.
- ❌ **Never** mix languages unless the trader does first.
- ❌ **Never** raise an exception out of the agent loop to the webhook
  handler. Catch, log, return an apologetic reply.
- ❌ **Never** discuss politics, news, competitors, medical/legal/relationship
  advice, or anything outside the rail guard scope.
- ❌ **Never** log raw account numbers, full inbound message bodies, or
  PINs (when present) to long-lived logs.

---

## 14. Demo Flow Reference

The 5-minute demo (CLAUDE.md §19) exercises minutes 3–4 through this agent:

- Minute 2 (post-claim): trader receives the bot's transfer-claim
  notification with order details + wa.me deep link
- Minute 3: trader sends `confirm AAJE-X` → direct-command path →
  status changes to `confirmed` → bot replies to trader only
- Minute 3 (continued): trader taps the wa.me link → personal WhatsApp
  opens to the buyer with the pre-filled template; trader sends/edits.
  The bot has no role in the trader↔buyer chat.
- Minute 4: trader sends `delivered AAJE-X` → direct-command path →
  status `delivered`
- Minute 5: trader sends `my BizPrint` → LLM agent loop → `get_bizprint`
  tool → score, grade, one-sentence insight

These turns must each complete inside the latency contract (§2) and use
the trader's preferred language. They are the agent's smoke test.

---

*Last updated: May 2026 — Twilio MVP pivot*
*This file pairs with CLAUDE.md. Section 3 (system prompt) MUST be identical*
*in both files. Update both in the same commit, or the agent will drift.*
