Step 2 — SQLAlchemy models & test for AAJE Storefront

Files added under `app/models/`:
- `store.py` — `Store` model mirroring `stores` table
- `product.py` — `Product` model mirroring `products` table
- `order.py` — `Order` model mirroring `orders` table
- `order_item.py` — `OrderItem` model mirroring `order_items` table
- `inventory_movement.py` — `InventoryMovement` model mirroring `inventory_movements` table
- `test_create_storefront_tables.py` — small script to run `Base.metadata.create_all`

Also updated `app/models/__init__.py` to export the new models.

Notes:
- Models follow the existing project's style (UUID PKs, `server_default=func.now()` timestamps).
- `order_items.total_price` is stored as a numeric column; business logic will set it on create/update.
- After running the test script the database should include the storefront tables from both migrations and SQLAlchemy models.

Next steps I will take:
1. Implement `services/` modules: `store_service.py`, `product_service.py`, `order_service.py`, `inventory_service.py`.
2. Add API routes under `routes/` for store/product/order management.
3. Implement Squad payment integration scaffold and webhook handling.
