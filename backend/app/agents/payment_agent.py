import uuid

from sqlalchemy import insert, select

from app.models.transaction import Transaction
from app.models.user import User
from app.redis import save_session
from app.services.squad import transfer
from app.services.whatsapp_client import send_text
from app.utils.formatters import format_naira


async def handle_add_supplier(whatsapp_no: str, message: str, session: dict):
    await handle_payment(whatsapp_no, message, session)


async def handle_payment(whatsapp_no: str, message: str, session: dict):
    parts = [part.strip() for part in message.split(",")]
    if len(parts) >= 4:
        name, bank_code, account_number, amount = parts[:4]
        session.setdefault("pending_data", {})["payment"] = {
            "supplier_name": name,
            "bank_code": bank_code,
            "account_number": account_number,
            "amount": float(amount.replace(",", "")),
        }
        session["awaiting_pin"] = True
        session["pin_action"] = "payment"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, f"Pay {format_naira(float(amount.replace(',', '')))} to {name} ({account_number}). Enter your PIN to confirm.")
        return
    await send_text(whatsapp_no, "To pay a supplier, reply: Name, Bank Code, Account Number, Amount\nExample: Alhaji Musa, 058, 0123456789, 10000")


async def execute_payment(whatsapp_no: str, session: dict, db):
    result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
    user = result.scalar_one_or_none()
    data = session.get("pending_data", {}).get("payment", {})
    if not user or not data:
        await send_text(whatsapp_no, "Payment details were not found.")
        return

    reference = f"PAY-{uuid.uuid4().hex[:16].upper()}"
    amount = float(data["amount"])
    await transfer(amount, data["bank_code"], data["account_number"], data["supplier_name"], "AAJE supplier payment", reference)
    await db.execute(insert(Transaction).values(
        user_id=user.id,
        amount=amount,
        type="debit",
        narration=f"Supplier payment to {data['supplier_name']}",
        category="payment",
        source="payment",
        squad_transaction_ref=reference,
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        processed=True,
    ))
    await db.commit()
    session.get("pending_data", {}).pop("payment", None)
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, f"Payment successful. Ref: {reference}")
