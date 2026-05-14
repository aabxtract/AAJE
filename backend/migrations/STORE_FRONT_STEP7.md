Step 7 — WhatsApp notification hooks

Changes made:
- `app/services/ai_store_builder.py`: after creating a store, sends a CTA message with the public store URL to `store.contact_whatsapp` (if `settings.app_public_url` set).
- `app/services/order_service.py`: after marking an order paid, sends a payment notification to the store owner's WhatsApp number.
- `app/services/inventory_service.py`: after decreasing stock, if `stock_quantity` <= `low_stock_threshold`, sends a low-stock alert to the store owner.

Notes:
- Notifications use existing `app.services.whatsapp_client` functions (`send_cta_button`, `send_text`).
- All notification calls are best-effort and wrapped in try/except to avoid failing main transaction flows.

Next steps:
1. Add configurable templates for notification messages and localization.
2. Add tests that mock WhatsApp API to assert messages are sent.
3. Wire WhatsApp actions (create my store, add product, show orders) into bot flows.
