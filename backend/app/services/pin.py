from passlib.context import CryptContext

from app.redis import clear_pin_attempts, increment_pin_attempts, save_session
from app.services.whatsapp_client import send_text

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)

INVALID_PINS = {
    "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888",
    "9999", "0000", "1234", "4321", "1212", "2580",
}


def hash_pin(pin: str) -> str:
    return pwd_context.hash(pin)


def verify_pin(pin: str, hashed: str) -> bool:
    if not hashed:
        return False
    return pwd_context.verify(pin, hashed)


def is_valid_pin(pin: str) -> bool:
    return pin.isdigit() and len(pin) == 4 and pin not in INVALID_PINS


async def handle_pin_input(whatsapp_no: str, pin_input: str, session: dict):
    from sqlalchemy import select

    from app.database import AsyncSessionLocal
    from app.models.user import User

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
        user = result.scalar_one_or_none()
        if not user:
            await send_text(whatsapp_no, "User not found.")
            return

        if verify_pin(pin_input.strip(), user.pin_hash):
            await clear_pin_attempts(whatsapp_no)
            action = session.get("pin_action")
            session["awaiting_pin"] = False
            session["pin_action"] = None
            await save_session(whatsapp_no, session)

            if action == "withdrawal":
                from app.agents.withdrawal_agent import execute_withdrawal

                await execute_withdrawal(whatsapp_no, session, db)
            elif action == "payment":
                from app.agents.payment_agent import execute_payment

                await execute_payment(whatsapp_no, session, db)
            return

        attempts = await increment_pin_attempts(whatsapp_no)
        if attempts >= 3:
            session["stage"] = "LOCKED"
            await save_session(whatsapp_no, session)
            await send_text(whatsapp_no, "Too many wrong PIN attempts. Your account is locked. A team member will contact you.")
            return

        await send_text(whatsapp_no, f"Wrong PIN. {3 - attempts} attempt(s) remaining.")
