import bcrypt

from app.redis import clear_pin_attempts, increment_pin_attempts, save_session
from app.services.whatsapp_client import send_text

INVALID_PINS = {
    "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888",
    "9999", "0000", "1234", "4321", "1212", "2580",
}


def hash_pin(pin: str) -> str:
    salt = bcrypt.gensalt()
    # bcrypt requires bytes
    hashed = bcrypt.hashpw(pin.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        # bcrypt requires bytes
        return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


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
            session["pending_flow"] = None
            await save_session(whatsapp_no, session)
            await send_text(whatsapp_no, "PIN verified. Complete sensitive operations in the secure browser flow.")
            return

        attempts = await increment_pin_attempts(whatsapp_no)
        if attempts >= 3:
            session["stage"] = "LOCKED"
            await save_session(whatsapp_no, session)
            await send_text(whatsapp_no, "Too many wrong PIN attempts. Your account is locked. A team member will contact you.")
            return

        await send_text(whatsapp_no, f"Wrong PIN. {3 - attempts} attempt(s) remaining.")
