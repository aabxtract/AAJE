from passlib.context import CryptContext
from app.redis import increment_pin_attempts, clear_pin_attempts
from app.redis import save_session
from app.services.twilio_client import send_text

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

INVALID_PINS = [
    "1111", "2222", "3333", "4444", "5555",
    "6666", "7777", "8888", "9999", "0000",
    "1234", "4321", "1212", "2580"
]

def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)

def verify_pin(pin: str, hashed: str) -> bool:
    return pwd_context.verify(pin, hashed)

def is_valid_pin(pin: str) -> bool:
    if not pin.isdigit():
        return False
    if len(pin) != 4:
        return False
    if pin in INVALID_PINS:
        return False
    return True

async def handle_pin_input(
    whatsapp_no: str,
    pin_input: str,
    session: dict
):
    from app.database import AsyncSessionLocal
    from sqlalchemy import select
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.whatsapp_no == whatsapp_no)
        )
        user = result.scalar_one_or_none()

        if not user:
            await send_text(whatsapp_no, "User not found.")
            return

        if verify_pin(pin_input, user.pin_hash):
            await clear_pin_attempts(whatsapp_no)
            session["awaiting_pin"] = False
            action = session.get("pin_action")
            session["pin_action"] = None
            await save_session(whatsapp_no, session)

            # Execute the gated action
            if action == "withdrawal":
                from app.agents.withdrawal_agent import execute_withdrawal
                await execute_withdrawal(whatsapp_no, session, db)
            elif action == "pay_supplier":
                from app.agents.payment_agent import execute_payment
                await execute_payment(whatsapp_no, session, db)
            elif action == "move_vault":
                from app.agents.vault_agent import execute_vault_move
                await execute_vault_move(whatsapp_no, session, db)
        else:
            attempts = await increment_pin_attempts(whatsapp_no)

            if attempts >= 3:
                session["stage"] = "LOCKED"
                await save_session(whatsapp_no, session)
                await send_text(
                    whatsapp_no,
                    "❌ Too many wrong PIN attempts. "
                    "Your account is temporarily locked. "
                    "A team member will contact you shortly."
                )
                from app.agents.support_agent import trigger_escalation
                await trigger_escalation(
                    whatsapp_no,
                    "PIN locked — 3 failed attempts",
                    "pin_lockout",
                    session
                )
            else:
                remaining = 3 - attempts
                await send_text(
                    whatsapp_no,
                    f"❌ Wrong PIN. {remaining} attempt(s) remaining."
                )
