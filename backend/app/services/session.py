"""
Session router — the brain of AAJE.

Reads session state from Redis and dispatches the inbound message
to the correct handler:

  ESCALATED         → hold message, tell trader a human is coming
  Not onboarded     → onboarding_agent
  Awaiting PIN      → pin service (intercepts before intent routing)
  Image received    → OCR service
  Onboarded/active  → intent classification → correct agent
"""
import logging

from app.redis import get_session, save_session
from app.services.twilio_client import send_text

logger = logging.getLogger(__name__)


async def route_message(
    whatsapp_no: str,
    message: str,
    media_url: str | None,
    media_type: str | None,
):
    session = await get_session(whatsapp_no)

    # If account is escalated, hold all messages
    if session.get("stage") == "ESCALATED":
        await send_text(
            whatsapp_no,
            "A team member is reviewing your case. "
            "Please wait — we'll respond shortly.",
        )
        return

    # Route based on onboarding status
    if not session.get("onboarding_complete"):
        from app.agents.onboarding_agent import handle_onboarding
        await handle_onboarding(whatsapp_no, message, session)
        return

    # Onboarding complete — check for PIN-gated action in progress
    if session.get("awaiting_pin"):
        from app.services.pin import handle_pin_input
        await handle_pin_input(whatsapp_no, message, session)
        return

    # Image → OCR
    if media_url and media_type and "image" in media_type:
        from app.services.ocr import process_receipt
        await process_receipt(whatsapp_no, media_url)
        return

    # Detect intent and route to correct agent
    from app.utils.message_parser import detect_intent
    intent = detect_intent(message, session.get("language", "en"))

    logger.info("Intent: %s | from: %s", intent, whatsapp_no)

    # Check frustration before routing
    from app.utils.frustration import detect_frustration
    if detect_frustration(message, session.get("language", "en")):
        from app.agents.support_agent import trigger_escalation
        await trigger_escalation(
            whatsapp_no, message, "frustration", session
        )
        return

    # Intent → agent dispatch
    from app.agents.insight_agent import handle_summary
    from app.agents.withdrawal_agent import handle_withdrawal
    from app.agents.payment_agent import handle_payment
    from app.agents.support_agent import handle_support
    from app.agents.vault_agent import handle_vault

    routes = {
        "greeting": handle_summary,
        "summary": handle_summary,
        "vault_balance": handle_vault,
        "withdraw": handle_withdrawal,
        "pay_supplier": handle_payment,
        "add_supplier": handle_payment,
        "move_vault": handle_vault,
        "help": handle_support,
        "trader_score": handle_summary,
    }

    handler = routes.get(intent, handle_support)
    await handler(whatsapp_no, message, session)
