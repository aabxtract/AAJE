from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import webhook, mono_webhook, admin

app = FastAPI(
    title="AAJE API",
    description="Financial operating system for Nigerian informal traders",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(webhook.router, prefix="/webhook", tags=["Twilio Webhook"])
app.include_router(mono_webhook.router, prefix="/mono", tags=["Mono Webhook"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}
