from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User
from app.redis import get_session, save_session
from app.services.whatsapp_client import send_cta_button, send_text
from app.utils.frustration import detect_frustration
from app.utils.rail_guard import is_in_scope, off_topic_response


async def route_message(whatsapp_no: str, message: str, db: AsyncSession) -> None:
    message = (message or "").strip()
    if not message:
        return

    session = await get_session(whatsapp_no)
    stage = session.get("stage", "NEW")
    user_id = session.get("user_id")

    if stage == "NEW" or not user_id:
        await _handle_unlinked(whatsapp_no)
        return

    if stage == "LOCKED":
        await send_text(whatsapp_no, "Your account is locked. Please contact AAJE support.")
        return

    if session.get("awaiting_pin"):
        await _handle_pin(whatsapp_no, message, session, db)
        return

    if not is_in_scope(message):
        await send_text(whatsapp_no, off_topic_response())
        return

    if detect_frustration(message):
        await send_text(
            whatsapp_no,
            "I can see this is frustrating. Type *help* to see what AAJE can do, or visit your dashboard.",
        )
        return

    await _handle_active(whatsapp_no, message, session, db)


async def _handle_unlinked(whatsapp_no: str) -> None:
    frontend = (settings.frontend_url or "https://aaje.store").rstrip("/")
    body = (
        "Welcome to AAJE — the business OS for Nigerian traders.\n\n"
        "Connect your account to manage your store, track orders, and check your balance from WhatsApp."
    )
    try:
        await send_cta_button(
            to=whatsapp_no,
            body=body,
            label="Connect AAJE",
            url=f"{frontend}/signup",
        )
    except Exception:
        await send_text(whatsapp_no, f"{body}\n\nCreate your account: {frontend}/signup")


async def _handle_pin(
    whatsapp_no: str, message: str, session: dict, db: AsyncSession
) -> None:
    from app.services.pin import handle_pin_input

    user_id = session.get("user_id")
    user = await db.get(User, user_id)
    if not user or not user.pin_hash:
        await send_text(whatsapp_no, "Account error. Please re-link your AAJE account.")
        return
    await handle_pin_input(message.strip(), whatsapp_no, user.pin_hash, session)


async def _handle_active(
    whatsapp_no: str, message: str, session: dict, db: AsyncSession
) -> None:
    # Phase 5: structured tool-calling agent brain.
    # Stub for Phase 1 — confirms two-way connection is live.
    text = message.lower().strip()
    if text in {"hi", "hello", "hey", "start", "menu", "help"}:
        user_id = session.get("user_id")
        user = await db.get(User, user_id)
        name = user.full_name.split()[0] if user and user.full_name else "there"
        await send_text(
            whatsapp_no,
            f"Hi {name}! AAJE is connected. ✅\n\n"
            "You can ask me about:\n"
            "- Your orders and sales\n"
            "- Your wallet balance\n"
            "- Adding or updating products\n"
            "- Your store link\n"
            "- Your BizPrint score\n"
            "- Withdrawing funds\n\n"
            "Full AI command support is coming soon.",
        )
        return

    await send_text(
        whatsapp_no,
        "AAJE received your message.\n\nType *help* to see available options.",
    )
