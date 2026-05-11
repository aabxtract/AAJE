import logging

from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.user import User
from app.redis import clear_mono_pending
from app.services.whatsapp_client import send_text

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/webhook/mono")
async def mono_webhook(request: Request, mono_webhook_secret: str = Header(default="", alias="mono-webhook-secret")):
    if mono_webhook_secret != settings.mono_webhook_secret:
        raise HTTPException(status_code=403, detail="Invalid Mono webhook secret")

    event = await request.json()
    event_type = event.get("event")
    data = event.get("data", {})
    logger.info("Mono event received: %s", event_type)

    if event_type == "mono.events.account_connected":
        reference = data.get("reference") or data.get("customer", {}).get("reference")
        account_id = data.get("account", {}).get("_id") or data.get("account_id")
        whatsapp_no = data.get("customer", {}).get("phone") or data.get("phone")
        async with AsyncSessionLocal() as db:
            user = None
            if reference:
                user = await db.get(User, reference)
            if not user and whatsapp_no:
                result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
                user = result.scalar_one_or_none()
            if user and account_id:
                user.mono_account_id = account_id
                await db.commit()
                await clear_mono_pending(user.whatsapp_no)
                await send_text(user.whatsapp_no, "Your bank connection is confirmed. Return to WhatsApp to continue.")

    return {"status": "received"}
