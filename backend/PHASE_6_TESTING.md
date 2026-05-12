# AAJE Phase 6 Deployment And Integration Checklist

## Render

1. Push the `complete-phases-4-6` branch to GitHub.
2. Create a Render web service from the repo.
3. Use `backend` as the root directory.
4. Confirm Render detects `runtime.txt` and uses Python 3.12.
5. Build command: `pip install -r requirements.txt`.
6. Start command: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`.
7. Add every variable from `.env.example` in the Render dashboard.
8. Deploy and confirm `GET /health` returns `{"status":"ok","environment":"production"}`.

## Webhooks

1. Meta WhatsApp webhook URL: `https://YOUR_RENDER_URL/webhook/whatsapp`.
2. Squad webhook URL: `https://YOUR_RENDER_URL/webhook/squad`.
3. Mono webhook URL: `https://YOUR_RENDER_URL/webhook/mono`.

## Integration Tests

1. Full onboarding with two streams.
2. Squad test payment and auto-split.
3. WhatsApp balance check.
4. Withdrawal with PIN gate.
5. Supplier payment with PIN gate.
6. `GET /economic-score/{user_id}` with `Authorization: Bearer ADMIN_TOKEN`.
7. Dashboard overview, user table, user modal, and stream chart.
8. Yoruba flow for onboarding through withdrawal.
9. PIN lockout after three wrong attempts.
10. Frustration escalation message and session stage.
