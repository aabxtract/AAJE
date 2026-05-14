Step 6 — Squad Intelligence sync client and wiring

Files added/updated:
- `app/services/intelligence_client.py` — async HTTP client using `httpx` that POSTs events to `settings.squad_base_url/intelligence/events` with optional `squad_secret_key` authorization header.
- `app/services/intelligence_sync.py` — updated to call `intelligence_client.send_event` and log failures.

Behavior:
- Events emitted from services (e.g., order_created, payment_confirmed) are now forwarded to the configured Squad Intelligence endpoint.
- Currently events are sent synchronously from the request flow; for production we should add queuing, batching, retries, and error handling.

Next recommended steps:
1. Add a reliable queue (Redis or DB table) and background worker to retry failed events.
2. Add metrics and monitoring around event delivery.
3. Update Squad Intelligence endpoint and auth details in `app/config.py` or environment.
