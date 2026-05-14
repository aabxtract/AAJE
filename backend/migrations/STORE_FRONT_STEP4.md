Step 4 — Product, Order, and Inventory services + routes

Files added:
- `app/services/product_service.py` — create/list/get products
- `app/services/inventory_service.py` — record movements, decrease/increase stock
- `app/services/order_service.py` — create orders, mark order paid (adjusts inventory)
- `app/services/intelligence_sync.py` — placeholder emitter for Squad Intelligence events
- `app/routes/product_routes.py` — endpoints to add/list products
- `app/routes/order_routes.py` — endpoints to create orders and mark paid

Behavior implemented:
- Creating an order records `Order` and `OrderItem` rows and emits an `order_created` event.
- Marking an order paid updates order state, reduces inventory per item, records `inventory_movements`, and emits a `payment_confirmed` event.
- Inventory adjustments use `decrease_stock` / `increase_stock` helpers and store movements in `inventory_movements` table.

Notes & next steps:
- Payment integration with Squad remains to be implemented; currently `mark_paid` can be used as a webhook/test hook to simulate payment confirmation.
- Next: implement Squad payment service and webhook handler, then connect intelligence sync to real Squad Intelligence API and WhatsApp notification hooks.
