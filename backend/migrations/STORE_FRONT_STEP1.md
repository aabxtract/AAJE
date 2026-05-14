Step 1 — Database schema & migration for AAJE Storefront

Files added:
- backend/migrations/002_storefront.sql

What I added in this step:
- Created SQL migration that defines the following tables:
  - `stores`: store meta (owner, name, slug, theme, contact, active flag)
  - `products`: product catalog linked to `stores` (price, stock, low threshold)
  - `orders`: core order record with payment and status fields
  - `order_items`: line items for orders with unit and total prices
  - `inventory_movements`: ledger of stock changes with reasons and optional related order

- Added indexes to improve lookup performance.

Notes and rationale:
- Migration uses `uuid_generate_v4()` to match existing schema style.
- `theme_json` is stored as `JSONB` to allow AI-generated theme payloads.
- `order_items.total_price` uses a generated column for correctness.
- `inventory_movements.movement_type` is a simple string; we'll use enumerated values in code.

Next recommended steps (I'll proceed when you confirm):
1. Add SQLAlchemy model classes in `app/models/` for these tables.
2. Wire models into `app/models/__init__.py` and run `Base.metadata.create_all` locally.
3. Implement `inventory_service` to record movements and decrement stock on successful payments.
4. Create API routes and services for store/product/order management.

If you'd like, I will now create the SQLAlchemy model files and a small test script to verify metadata creation.
