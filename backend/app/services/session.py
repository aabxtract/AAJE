import logging

from app.redis import get_session, save_session
from app.services.whatsapp_client import send_text

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "Here is what you can ask me:\n"
    "1. balance\n"
    "2. withdraw\n"
    "3. pay supplier\n"
    "4. summary\n"
    "5. score"
)


async def route_message(whatsapp_no: str, message: str):
    session = await get_session(whatsapp_no)

    if session.get("stage") == "LOCKED":
        await send_text(whatsapp_no, "Your account is locked after too many wrong PIN attempts. A team member will contact you.")
        return

    if session.get("stage") == "ESCALATED":
        await send_text(whatsapp_no, "A team member is reviewing your case. Please wait.")
        return

    if not session.get("onboarding_complete"):
        from app.agents.onboarding_agent import handle_onboarding

        await handle_onboarding(whatsapp_no, message, session)
        return

    if session.get("awaiting_pin"):
        from app.services.pin import handle_pin_input

        await handle_pin_input(whatsapp_no, message, session)
        return

    pending_data = session.get("pending_data", {})
    if pending_data.get("withdrawal_flow"):
        from app.agents.withdrawal_agent import handle_withdrawal

        await handle_withdrawal(whatsapp_no, message, session)
        return

    if pending_data.get("payment_flow"):
        from app.agents.payment_agent import handle_payment

        await handle_payment(whatsapp_no, message, session)
        return

    from app.utils.frustration import detect_frustration

    if detect_frustration(message):
        session["stage"] = "ESCALATED"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, "I am connecting you to a team member. Someone will respond within 30 minutes.")
        return

    from app.utils.message_parser import detect_intent

    intent = detect_intent(message)
    logger.info("Intent %s from %s", intent, whatsapp_no)

    if intent in {"greeting", "balance"}:
        from app.agents.vault_agent import handle_balance_check

        await handle_balance_check(whatsapp_no, session)
    elif intent == "withdraw":
        from app.agents.withdrawal_agent import handle_withdrawal

        await handle_withdrawal(whatsapp_no, message, session)
    elif intent == "pay":
        from app.agents.payment_agent import handle_payment

        await handle_payment(whatsapp_no, message, session)
    elif intent == "add_supplier":
        from app.agents.payment_agent import handle_add_supplier

        await handle_add_supplier(whatsapp_no, message, session)
    elif intent == "summary":
        from app.agents.vault_agent import handle_summary

        await handle_summary(whatsapp_no, session)
    elif intent == "score":
        from app.agents.vault_agent import handle_score

        await handle_score(whatsapp_no, session)
    elif intent == "help":
        await send_text(whatsapp_no, HELP_TEXT)
    else:
        await send_text(whatsapp_no, f"I did not understand that.\n\n{HELP_TEXT}")
