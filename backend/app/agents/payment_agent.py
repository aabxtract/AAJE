from app.redis import save_session
from app.services.twilio_client import send_text
from app.models.payment import Payment

async def handle_payment(whatsapp_no: str, message: str, session: dict):
    await send_text(whatsapp_no, "To pay a supplier, reply with their Name, Bank Code, Account Number, and Amount.\nExample: Alhaji Musa, 058, 0123456789, 10000")
    session["stage"] = "PAYMENT_COLLECTION"
    await save_session(whatsapp_no, session)

async def execute_payment(whatsapp_no: str, session: dict, db):
    from app.services.squad import transfer
    from app.models.user import User
    from sqlalchemy import select
    
    user = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
    user = user.scalar_one_or_none()
    
    data = session.get("pending_data", {})
    amount = data.get("amount", 0)
    account = data.get("supplier_account")
    bank_code = data.get("supplier_bank")
    stream_id = data.get("stream_id")
    
    ref = f"pay_{user.id}_{int(amount)}"
    await transfer(account, bank_code, int(amount * 100), "Payment", ref)
    
    pmt = Payment(
        user_id=user.id,
        stream_id=stream_id,
        amount=amount,
        squad_transfer_ref=ref,
        status='completed'
    )
    db.add(pmt)
    await db.commit()
    
    await send_text(whatsapp_no, f"✅ Payment of ₦{amount:,.2f} to {account} was successful. Ref: {ref}")
