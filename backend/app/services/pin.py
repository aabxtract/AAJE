import bcrypt

from app.redis import clear_pin_attempts, increment_pin_attempts, save_session
from app.services.whatsapp_client import send_text

MAX_ATTEMPTS = 3
OBVIOUS_PINS = {
    "0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888",
    "9999", "1234", "4321", "1212", "2580",
}


def hash_pin(pin: str) -> str:
    return bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_pin(pin: str, hashed: str) -> bool:
    if not hashed:
        return False
    try:
        return bcrypt.checkpw(pin.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def is_valid_pin(pin: str) -> bool:
    return pin.isdigit() and len(pin) == 4 and pin not in OBVIOUS_PINS


async def handle_pin_input(pin: str, whatsapp_no: str, pin_hash: str, session: dict) -> None:
    if verify_pin(pin, pin_hash):
        await clear_pin_attempts(whatsapp_no)
        session["awaiting_pin"] = False
        session["pin_action"] = None
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, "PIN verified. You can continue.")
        return

    attempts = await increment_pin_attempts(whatsapp_no)
    if attempts >= MAX_ATTEMPTS:
        session["stage"] = "LOCKED"
        await save_session(whatsapp_no, session)
        await send_text(
            whatsapp_no,
            "Too many wrong PIN attempts. Your account is locked. Contact AAJE support to unlock.",
        )
        return

    remaining = MAX_ATTEMPTS - attempts
    await send_text(whatsapp_no, f"Wrong PIN. {remaining} attempt(s) remaining.")
