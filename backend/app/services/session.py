"""
Session router — the central hub that receives every inbound WhatsApp message
and dispatches it to the correct agent based on session state and intent.

Routing priority:
  1. Locked / Escalated → block
  2. Not onboarded → onboarding agent
  3. Awaiting PIN → PIN handler
  4. Frustration detected → escalation
  5. Intent-based routing → balance, withdraw, pay, summary, score, debrief, support, help
"""
import logging

from app.redis import get_session, save_session
from app.services.whatsapp_client import send_text

logger = logging.getLogger(__name__)

HELP_TEXT = (
    "Here is what you can do:\n\n"
    "💰 *balance* — check your vault balances\n"
    "💸 *withdraw* — withdraw to your bank\n"
    "🏪 *pay* — pay a supplier\n"
    "📊 *summary* — get a business insight\n"
    "📈 *score* — view your trader score\n"
    "📋 *debrief* — get your daily report\n"
    "🆘 *help* — see this menu\n"
    "🙋 *human* — speak to a team member"
)


async def route_message(whatsapp_no: str, message: str):
    session = await get_session(whatsapp_no)

    # 1. Account locked
    if session.get("stage") == "LOCKED":
        await send_text(
            whatsapp_no,
            "🔒 Your account is locked after too many wrong PIN attempts. "
            "A team member will contact you.",
        )
        return

    # 2. Escalated to human
    if session.get("stage") == "ESCALATED":
        await send_text(
            whatsapp_no,
            "A team member is reviewing your case. Please wait — "
            "they will respond on this chat.",
        )
        return

    # 3. Not yet onboarded
    if not session.get("onboarding_complete"):
        from app.agents.onboarding_agent import handle_onboarding

        await handle_onboarding(whatsapp_no, message, session)
        return

    # 4. Awaiting PIN confirmation for a sensitive action
    if session.get("awaiting_pin"):
        from app.services.pin import handle_pin_input

        await handle_pin_input(whatsapp_no, message, session)
        return

    # 5. Check for frustration BEFORE intent routing
    from app.utils.frustration import detect_frustration

    if detect_frustration(message):
        from app.agents.support_agent import trigger_escalation

        await trigger_escalation(whatsapp_no, message, "frustration", session)
        return

    # 6. Intent-based routing
    from app.utils.message_parser import detect_intent

    intent = detect_intent(message)
    logger.info("Intent '%s' from %s", intent, whatsapp_no)

    if intent == "greeting":
        from app.utils.phrases import get_phrase

        language = session.get("language", "en")
        await send_text(whatsapp_no, get_phrase("greeting", language))

    elif intent == "balance":
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

    elif intent == "debrief":
        from app.agents.insight_agent import handle_debrief

        await handle_debrief(whatsapp_no, session)

    elif intent == "support":
        from app.agents.support_agent import handle_support

        await handle_support(whatsapp_no, message, session)

    elif intent == "help":
        await send_text(whatsapp_no, HELP_TEXT)

    else:
        await send_text(
            whatsapp_no,
            f"I did not understand that. 🤔\n\n{HELP_TEXT}",
        )
