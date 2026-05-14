from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.commerce import Store
from app.models.user import User
from app.whatsapp.service import send_text

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


class SendRequest(BaseModel):
    to: str
    message: str


class ConnectStorefrontRequest(BaseModel):
    user_id: str
    store_id: str
    whatsapp_number: str
    premium: bool = False


@router.post("/send")
async def send_whatsapp(payload: SendRequest):
    return await send_text(payload.to, payload.message)


@router.post("/connect-storefront")
async def connect_storefront(payload: ConnectStorefrontRequest, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.user_id)
    store = await db.get(Store, payload.store_id)
    if not user or not store or store.user_id != user.id:
        raise HTTPException(status_code=404, detail="User/store connection not found")

    whatsapp_number = payload.whatsapp_number.strip()
    if not whatsapp_number:
        raise HTTPException(status_code=400, detail="WhatsApp number is required")

    user.whatsapp_no = whatsapp_number
    user.whatsapp_connected = True
    user.onboarding_complete = True
    user.persona_mode = "storefront_operations_premium" if payload.premium else "storefront_operations_free"
    store.contact_whatsapp = whatsapp_number
    store.whatsapp_number = whatsapp_number
    await db.commit()

    test_message = (
        f"AAJE WhatsApp is connected to {store.store_name}.\n\n"
        "You will receive order, payment, inventory, and sales updates here."
    )
    try:
        await send_text(whatsapp_number, test_message)
        notification_status = "sent"
    except Exception:
        notification_status = "failed"

    return {
        "status": "connected",
        "persona": user.persona_mode,
        "store_id": str(store.id),
        "whatsapp_number": whatsapp_number,
        "test_notification": notification_status,
    }


@router.post("/webhook")
async def whatsapp_webhook_alias():
    return {"status": "use /webhook/whatsapp for Meta verification and signed webhooks"}
