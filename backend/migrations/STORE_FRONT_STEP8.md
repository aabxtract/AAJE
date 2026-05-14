Step 8 — Minimal public storefront pages and routes

Files added:
- `app/routes/public_store.py` — public endpoints:
  - `GET /store/{slug}` — store homepage listing active products
  - `GET /store/{slug}/product/{product_id}` — product detail with simple checkout form
  - `POST /store/{slug}/checkout` — creates an order, returns a simulated Squad payment link

- `app/main.py` — router registration for the public storefront.

Notes:
- Pages are simple HTML returned directly from the endpoints (no template engine required).
- Checkout creates an `Order` and returns a payment link from `squad_payment_service.create_payment_link`.
- For production, add proper HTML templates, static assets, CSRF protections, and client-side UX.

Next steps:
1. Improve the UI with Jinja2 templates or a small frontend app.
2. Add tests for public routes and end-to-end flows.
3. Implement optional cart support if needed later.
