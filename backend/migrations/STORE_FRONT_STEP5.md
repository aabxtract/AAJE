Step 5 — Squad payment scaffold + webhook and E2E simulation

Files added:
- `app/services/squad_payment_service.py` — scaffold to create simulated payment links and verify webhooks.
- `app/routes/squad_webhook.py` — webhook endpoint that accepts Squad payment confirmations and calls `mark_order_paid`.
- `backend/scripts/run_end_to_end.py` — a runnable script that creates a test user, builds a store via the AI builder, adds starter products, places an order, simulates a payment link, and marks the order paid. It prints inventory before and after to verify stock decrement.

Notes:
- Payment integration is simulated; replace `create_payment_link` and `verify_webhook` with real Squad API calls and signature verification for production.
- The E2E script uses SQLAlchemy session directly and will run against the configured `settings.database_url` in `app/config.py`.

How to run the simulation locally (example):
```bash
# from repo root
cd backend
python -m backend.scripts.run_end_to_end
```

Next steps:
1. Implement robust Squad API client and secure webhook verification.
2. Implement Intelligence sync integration with Squad Intelligence API (event batching, retries).
3. Add WhatsApp notification hooks to notify traders.
