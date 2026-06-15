# userflow-and-UI-fix.md — Frontend Overhaul Plan

> Captures the seven asks from the May 23 conversation. Each ask is restated
> (so the user can confirm I understood), decoded into concrete file-level
> changes, and ordered for implementation.
>
> **Read before writing code.** Open questions at the end MUST be answered
> before any of this gets built — premature work here is wasted work.

---

## What the user said (verbatim, condensed)

1. **Remove the pricing tab before publishing.** The plan picker between
   "Confirm" and "Publish" has to go.
2. **Subdomain architecture, not route paths.** Stores should live at
   `{slug}.aaje.store`, not `aaje.store/store/{slug}`.
3. **Post-signup AI UI is wrong.** Currently a chat-bubble interface.
   Should be a **pop-up message bar** with a placeholder input — AI shows
   one prompt, trader types one answer, repeat.
4. **The LLM looks scripted.** Right now Python decides which question
   comes next (`QUESTIONS` array) and what suggestions appear (`AI_SUGGESTIONS`
   dict). Remove all those boundaries — the LLM should drive the entire
   conversation, pick what to ask, when to suggest a template, when to
   declare onboarding done.
5. **Templates aren't working.** The current 5 templates render but feel
   wack. Need real templates.
6. **15 JSON templates.** Hand-craft ~15 distinct storefront designs as
   JSON. The LLM picks one (or suggests options) based on the trader's
   business.
7. **Confirm understanding + ask questions before implementing.** First
   produce this file. Then clarify. Then build.

---

## Decoded plan

### A. Pricing/plan removal (small)

- `frontend/storefront-web/src/pages/Publish.jsx`: drop the `PLANS` array,
  drop the plan-picker UI. After `/confirm` the user goes straight to
  "Publish your store" → single button → calls `createStore(...)` → routes
  to dashboard.
- `frontend/storefront-web/src/App.jsx`: the marketing `/pricing` route
  can stay (it's the public marketing page), but the onboarding flow no
  longer routes through it.
- `frontend/storefront-web/src/pages/ConfirmBuild.jsx`: change "Continue
  to plans" button to "Publish my store".

### B. Subdomain architecture (large)

Three pieces:

**B.1 — Routing.**
- New top-level `<App />` checks `window.location.hostname`.
- If hostname matches `(\w+)\.aaje\.store` (or `*.localtest.me` in dev),
  extract the subdomain and render `<StorePage slug={subdomain} />`
  directly. **No URL path needed.**
- If hostname is the apex (`aaje.store` or `localhost`), render the existing
  routes (`/`, `/signup`, `/admin/*`, etc.).
- Drop the `/store/:slug` route from the router entirely.

**B.2 — Dev workflow.**
- Use `*.localtest.me` (resolves to 127.0.0.1, no `/etc/hosts` edits).
  `npm run dev` already binds to 0.0.0.0 via Vite default — confirm.
- Buyer URL during dev: `http://<slug>.localtest.me:5174` (or :4173 for
  preview build).
- Vite config: must whitelist the wildcard host (`server.allowedHosts:
  ['.localtest.me', '.aaje.store']`).

**B.3 — Production (Vercel + DNS).**
- Vercel: add `*.aaje.store` as a wildcard domain on the Vite project.
- DNS: wildcard A/CNAME record pointing to Vercel.
- SSL: Vercel auto-provisions for wildcard.
- Backend CORS: change `allow_origins` to `allow_origin_regex=r"https://.*\.aaje\.store"`
  (we currently use exact-string list; needs the regex variant).

**B.4 — Admin location.**
- **Open question** (see end of doc): admin stays at `aaje.store/admin/*`
  or moves to `app.aaje.store`?

### C. Pop-up message bar UI (medium)

New component: `<AIPopupBar />` at `src/components/AIPopupBar.jsx`.

Visual treatment:
- Anchored to the **bottom-center** of the viewport.
- Width: `100%` on mobile, `max-w-2xl` centered on desktop.
- Two stacked sections:
  1. **AI message card** (top): the latest LLM message in a soft elevated
     card. Optional typewriter animation. Optional **quick-reply chips**
     beneath it (e.g. "Fashion", "Food", "Tech" — when the LLM offers a
     choice it adds these to its response).
  2. **Input row** (bottom): full-width text input with placeholder hint
     that the LLM controls ("Describe your business…", "What should we
     call your store?", etc.), plus a send button.
- States: `idle` (input enabled), `awaiting_ai` (input disabled, spinner
  in the AI card), `submitting` (input disabled, spinner on send).
- Voice input button (mic icon) — optional v2.
- Skip/back button — TBD with the user.

The old `Onboarding.jsx` chat-bubble UI gets **deleted** and replaced with
a single `<AIPopupBar />` over a calm gradient background showing the
trader's current progress (template preview pane).

### D. LLM-driven onboarding (large)

**Current state (the boundaries to remove):**
- `pages/Onboarding.jsx`: hardcoded `QUESTIONS` array (5 fixed questions
  in fixed order) + `AI_SUGGESTIONS` dict (canned product lists per
  business type)
- `services/store_generator.py`: strict JSON schema enforcement in the
  system prompt
- `intelligence/llm_client.py`: forces JSON output via `response_format`
- (Possibly) the agent rail guard for the WhatsApp side — **TBD**, may
  not apply to onboarding

**New flow:**
- New backend endpoint: `POST /onboarding/turn` taking
  `{ history: [{role: 'user'|'assistant', content: str}], user_id }`
  and returning `{ message: str, quick_replies?: [str], placeholder?: str, done: bool, store_config?: dict }`.
- The endpoint sends the conversation history to the LLM with a single
  system prompt:
  > You are the AAJE onboarding host. Your goal: produce a storefront
  > config for a Nigerian trader. You decide what to ask, in what order,
  > and when you have enough. Available templates: [list]. When you have
  > all you need, set done=true and include store_config.
- LLM is in tool-calling mode with two tools:
  - `list_templates()` → returns the 15 template metadata
  - `finalize_onboarding(store_name, slug, template_id, theme_overrides, products, hero_text, contact_whatsapp)` → returns the final store config
- No predefined question count. LLM might ask 3 questions or 12.
- Frontend just renders whatever the LLM returns into the `<AIPopupBar />`
  and POSTs the next answer.

When `done: true`, frontend calls `/store/setup` with the
`store_config` from the response.

### E. 15 JSON templates (medium)

Templates live at **`backend/app/intelligence/templates/*.json`**, not in
the frontend. Why backend: the LLM tool `list_templates` reads them, so
the source of truth is server-side. Frontend pulls metadata via an
endpoint, renders the chosen template via shared React components.

Each template JSON:
```json
{
  "template_id": "lagos_boutique",
  "name": "Lagos Boutique",
  "tagline": "Warm earth tones, hero grid, perfect for ankara and lace",
  "best_for": ["fashion", "boutique", "ankara", "lace"],
  "industry_keywords": ["fashion", "cloth", "wear", "boutique"],
  "theme_config": {
    "primary_color": "#7C2D12",
    "accent_color": "#F59E0B",
    "background": "#FAF8F5",
    "card_background": "#FFFFFF",
    "text_color": "#1C1917",
    "muted_text": "#78716C",
    "font_family": "serif",
    "border_radius": "rounded-2xl"
  },
  "layout": {
    "hero": "editorial_split",
    "product_grid": "2-col-tall",
    "show_search": true,
    "show_categories": true,
    "show_sort": true,
    "show_about": true
  },
  "default_sections": ["hero", "featured_products", "all_products", "about", "footer"],
  "suggested_categories": ["New In", "Dresses", "Accessories", "Sale"],
  "sample_hero_text": "Handcrafted ankara, ready in 48h.",
  "placeholder_imagery": ["fabric_close_up", "model_full_length"]
}
```

**The 15 templates** (with the niche each targets):

| # | template_id | Niche |
|---|------------|------|
| 1 | `lagos_boutique` | Fashion (warm earth + serif) |
| 2 | `naija_streetwear` | Streetwear (bold yellow + magazine) |
| 3 | `ankara_artisan` | Ankara (vibrant orange + purple) |
| 4 | `velvet_atelier` | Luxury wear (black + gold) |
| 5 | `computer_village_tech` | Tech (electric blue + density) |
| 6 | `phone_accessories` | Phone accessories (cyan + grid) |
| 7 | `tech_repair_hub` | Services (steel grey + service blocks) |
| 8 | `mama_kitchen` | Restaurant (green/red/white) |
| 9 | `food_truck` | Food vendor (warm orange + menu) |
| 10 | `provision_store` | Provisions (utility green + dense) |
| 11 | `sapphire_beauty` | Beauty (rose gold + soft cards) |
| 12 | `wellness_studio` | Wellness (sage green + calm) |
| 13 | `books_and_stationery` | Bookshop (academic burgundy) |
| 14 | `bouquet_florist` | Florist (pastel pink + gallery) |
| 15 | `creator_portfolio` | Creator/services (minimal mono + portfolio) |

Rendering side: collapse the current 5 template React components into
**one universal renderer** (`<TemplateRenderer template={json} />`) that
reads the JSON and produces the storefront. No more
`PremiumTemplate.jsx`/`FashionTemplate.jsx`/etc — those become dead.

### F. Removing LLM boundaries (medium, sensitive)

The bounds we're dropping:
- `pages/Onboarding.jsx` scripted `QUESTIONS` array → gone (D above)
- `pages/Onboarding.jsx` `AI_SUGGESTIONS` lookup → gone
- `services/store_generator.py` strict-JSON system prompt → relaxed; LLM
  returns a config via tool call, not via JSON-string parsing
- `intelligence/llm_client.py` `response_format={"type": "json_object"}`
  on store generation → dropped for onboarding (kept for non-conversation
  paths if any remain)

The bounds we're **keeping** (subject to user confirmation):
- WhatsApp agent rail guard (CLAUDE.md §16) — refuses off-topic chat.
  This is product safety, not "scripting the LLM". I recommend keeping.
- PII scrubber before every LLM call — non-negotiable, security rule.
- 150-word response cap in the WhatsApp agent prompt — keep, this is
  WhatsApp UX, not creativity restriction.
- Tool-use mode itself — keep. "LLM decides everything" doesn't mean
  no tools; it means no scripted question-flow.

---

## Implementation order

1. **F1**: Drop the pricing/plan step (cheapest, unblocks #2)
2. **E**: Write the 15 template JSONs + the universal renderer (parallel-safe)
3. **D**: Build `/onboarding/turn` backend endpoint + delete onboarding script
4. **C**: Build `<AIPopupBar />` component (depends on D's response shape)
5. **B**: Switch to subdomain routing (depends on E's renderer being stable)
6. **F-cleanup**: Remove dead template components, dead onboarding scripts
7. **Smoke test**: Repeat the 47-check suite + manual walkthrough

Estimated total: 6–9 hours of focused work depending on the open-question
answers below.

---

## Decisions (locked, May 23)

1. **Pop-up bar interaction**: one question at a time, NO scrolling
   history. Calm gradient background with a live template preview pane
   above the bar. Quick-reply chips appear when the LLM offers options;
   trader can tap a chip OR type free-form.
2. **LLM boundaries**: drop the scripted onboarding flow. The LLM gets a
   **content manual** (a rich system prompt + tool definitions) that
   describes the goal, the available templates, and the finalize step —
   but the LLM picks its own questions, makes its own suggestions, and
   decides when it has enough. The PII scrubber and the WhatsApp-side
   rail guard stay (they're security/safety, not "scripting" — the user
   said "should be able to do all that it should do" which I read as full
   conversational autonomy inside the safety rails, not removing the
   safety rails themselves).
3. **Subdomain + admin**: dev uses `<slug>.localtest.me:5174` (zero
   config). Admin stays at `aaje.store/admin/*` on apex (no
   `app.aaje.store` for MVP). Buyers visit `<slug>.aaje.store` in prod.
4. **Template browsing**: LLM picks one, then offers a "see other styles"
   chip the trader can tap to browse the alternatives as quick-reply
   chips. No upfront gallery.

## Defaults applied to the remaining open questions

These were not explicitly answered. I'm applying the safest default and
proceeding — flag anything you disagree with.

- **Apex `aaje.store`** → renders the existing `<Landing />` marketing page.
- **Old `/store/:slug` URLs** → 301 redirect to `<slug>.aaje.store` so
  shared links keep working.
- **Dashboard / orders / products / payout-account UI** → unchanged.
- **Skip / back button on the pop-up bar** → not in v1. Trader has to
  proceed forward or refresh to restart.

---

## Open questions (decided above — kept for reference)

These are the decisions where my recommendation could be wrong. I am NOT
going to start coding any of the above until these are settled.

1. **Dev subdomain strategy** — `localtest.me` (zero config, just works)
   vs `/etc/hosts` entries (requires admin, manual per slug). Recommend
   `localtest.me`. Confirm?

2. **Admin location** — `aaje.store/admin/*` (current) or `app.aaje.store`?
   The latter requires another wildcard branch in DNS. Recommend keeping
   admin on apex root for MVP.

3. **Pop-up bar interaction model** — (a) one question at a time, no
   visible history; (b) show full chat history scrolling above the input;
   (c) one question at a time but with a "back" button to revisit prior
   answers. Recommend (a) for the "pop-up bar" feel — minimal, focused.

4. **Quick-reply chips when LLM offers options** — yes (LLM can attach
   suggestions to its messages, trader taps a chip OR types) or no
   (always free-text)? Recommend yes — speeds up template selection.

5. **LLM boundaries to actually keep** —
   - Rail guard on WhatsApp agent: keep (product safety)? **Y/N**
   - PII scrubber on every LLM call: keep (security)? **Y/N**
   - 150-word WhatsApp response cap: keep (UX)? **Y/N**
   If you say no to any, I need a clear safety story for what replaces
   them.

6. **Templates: trader override** — should the trader be able to
   manually pick a template ("show me other options") or only get the
   LLM's recommendation? Recommend allow override via a "see other
   styles" chip the LLM can offer.

7. **Existing dashboard/admin UI** — out of scope here, right? You said
   the post-signup AI flow is wack, but the dashboard, orders page,
   products page, payout-account form all stay as-is for now?

8. **Subdomain on apex `aaje.store`** — what should the apex render?
   - (a) Marketing/landing page (`<Landing />`, current behavior)
   - (b) Redirect to `app.aaje.store` if admin moves there
   Recommend (a).

9. **Existing storefront URLs (`/store/:slug`)** — break them (return 404)
   or 301 to the subdomain? Recommend 301 so any shared old links don't
   die.

---

## Out of scope (explicit)

These are decidedly NOT part of this overhaul:
- WhatsApp agent loop changes (rail guard, system prompt, tools)
- Payout-account form, order management UI, dashboard widgets
- Twilio integration, ngrok config, Supabase schema
- The `.claude/fix.md` Steps 5–10 (status badges, BizPrint widget,
  production deploy) — those continue afterward
