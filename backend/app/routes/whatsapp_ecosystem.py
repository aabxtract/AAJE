from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.commerce import Store
from app.models.user import User
from app.services.whatsapp_client import send_text

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


class SendRequest(BaseModel):
    to: str
    message: str


class ConnectStorefrontRequest(BaseModel):
    user_id: str
    store_id: str


@router.post("/send")
async def send_whatsapp(payload: SendRequest):
    return await send_text(payload.to, payload.message)


@router.post("/connect-storefront")
async def connect_storefront(payload: ConnectStorefrontRequest, db: AsyncSession = Depends(get_db)):
    user = await db.get(User, payload.user_id)
    store = await db.get(Store, payload.store_id)
    if not user or not store or store.user_id != user.id:
        raise HTTPException(status_code=404, detail="User/store connection not found")
    user.persona_mode = "storefront_extension"
    store.contact_whatsapp = user.whatsapp_no
    return {"status": "connected", "persona": user.persona_mode, "store_id": str(store.id)}


@router.post("/webhook")
async def whatsapp_webhook_alias():
    return {"status": "use /webhook/whatsapp for Meta verification and signed webhooks"}
