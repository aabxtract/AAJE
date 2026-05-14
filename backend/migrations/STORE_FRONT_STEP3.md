Step 3 — AI Store Builder service and API routes

Files added:
- `app/services/ai_store_builder.py` — service that generates AI-style store payloads and creates `Store` and starter `Product` rows in DB.
- `app/routes/ai_store_routes.py` — FastAPI router with two endpoints:
  - `POST /ai/store/build` — returns a suggested payload (no DB changes)
  - `POST /ai/store/create` — creates store and starter products in database

Usage notes:
- The builder currently uses deterministic heuristics and simple templates (no external LLM calls). It returns the JSON structure described in the build spec.
- `create_store` expects a DB session (`AsyncSession`) and a `user_id` (UUID string). It will persist the `Store` and optional starter `Product` items.

Next steps I'll implement:
1. Product, order, and inventory routes and services (CRUD + inventory movement logging).
2. Squad payment integration scaffold and webhook handling.
3. Intelligence sync service to emit events after commerce actions.
