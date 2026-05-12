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

from app.redis import clear_session, clear_state_history, get_session, pop_state_history, save_session
from app.services.whatsapp_client import send_text, send_translated

logger = logging.getLogger(__name__)

RESET_COMMANDS = {"restart", "reset", "start over", "start again", "begin again"}

BACK_COMMANDS = {"back", "undo", "go back", "previous", "prev", "return"}

# Prompt to re-send when the user lands back on a given stage
_STAGE_REPROMPT: dict[str, str] = {
    "SELECTING_LANGUAGE": (
        "Let's go back ↩\n\n"
        "Choose your language:\n1. Yoruba\n2. Igbo\n3. Hausa\n4. Pidgin\n5. English"
    ),
    "COLLECTING_NAME": "Let's go back ↩\n\nWhat is your full name?",
    "COLLECTING_LOCATION": "Let's go back ↩\n\nWhat market or town do you trade in?",
    "COLLECTING_BUSINESS_TYPE": (
        "Let's go back ↩\n\nWhat type of business do you run?\n"
        "1. Market Trader\n2. Food Vendor\n3. Shop Owner\n4. Artisan\n5. Other"
    ),
    "COLLECTING_ACCOUNT": (
        "Let's go back ↩\n\nEnter your account number and bank.\n"
        "Example: 0123456789 GTBank"
    ),
    "CONFIRMING_IDENTITY": (
        "Let's go back ↩\n\nEnter your account number and bank again.\n"
        "Example: 0123456789 GTBank"
    ),
    "CONNECTING_BANK": (
        "Let's go back ↩\n\nTap *Connect Bank* to link your account, "
        "or reply *skip* to continue without it."
    ),
    "COLLECTING_STREAM_COUNT": (
        "Let's go back ↩\n\nDo you run more than one business?\nReply 1 for Yes, 2 for No."
    ),
    "COLLECTING_STREAM_NAMES": "Let's go back ↩\n\nName your business.",
    "CONFIGURING_SPLITS": (
        "Let's go back ↩\n\nWhat percentage of your income should go to each account?\n"
        "All percentages must add up to 100%."
    ),
    "CREATING_PIN": "Let's go back ↩\n\nCreate a 4-digit PIN to secure your account.",
    "CONFIRMING_PIN": "Let's go back ↩\n\nConfirm your PIN. Enter it again.",
    "POLICY_ACCEPTANCE": (
        "Let's go back ↩\n\nReply *I Accept* to activate your account, "
        "or *back* to change something."
    ),
}

# Ordered list of onboarding stages (earliest → latest)
_ONBOARDING_STAGE_ORDER = [
    "NEW",
    "SELECTING_LANGUAGE",
    "COLLECTING_NAME",
    "COLLECTING_LOCATION",
    "COLLECTING_BUSINESS_TYPE",
    "COLLECTING_ACCOUNT",
    "CONFIRMING_IDENTITY",
    "CONNECTING_BANK",
    "COLLECTING_STREAM_COUNT",
    "COLLECTING_STREAM_NAMES",
    "CREATING_ACCOUNTS",
    "CONFIGURING_SPLITS",
    "CREATING_PIN",
    "CONFIRMING_PIN",
    "POLICY_ACCEPTANCE",
]

# pending_data keys to erase when going back FROM a stage
# (i.e. the data that was collected *during* that stage)
_CLEAR_ON_BACK_FROM: dict[str, list[str]] = {
    "SELECTING_LANGUAGE":       ["language"],
    "COLLECTING_NAME":          ["full_name"],
    "COLLECTING_LOCATION":      ["location"],
    "COLLECTING_BUSINESS_TYPE": ["business_type"],
    "COLLECTING_ACCOUNT":       [
        "account_number", "bank_code", "bank_display",
        "verified_name",
    ],
    "CONFIRMING_IDENTITY":      [
        "verified_bank_account", "verified_bank_code", "verified_bank_name",
        "squad_customer_id",
    ],
    "CONNECTING_BANK":          [],           # no pending_data written here
    "COLLECTING_STREAM_COUNT":  ["stream_count", "streams"],
    "COLLECTING_STREAM_NAMES":  ["streams"],
    "CREATING_ACCOUNTS":        ["streams"],  # will be recreated
    "CONFIGURING_SPLITS":       ["split_index"],
    "CREATING_PIN":             ["pin_hash"],
    "CONFIRMING_PIN":           ["pin_hash"],
    "POLICY_ACCEPTANCE":        [],
}


async def _synthetic_back(whatsapp_no: str, session: dict) -> str | None:
    """
    Fallback revert when the Redis history stack is empty.

    Steps the session back one position in the known onboarding stage order,
    clears the pending_data that was written during the stage being undone,
    saves the mutated session to Redis, and returns the reprompt text.

    Returns None if the user is already at the earliest possible stage.
    """
    current_stage = session.get("stage", "NEW")
    try:
        idx = _ONBOARDING_STAGE_ORDER.index(current_stage)
    except ValueError:
        return None  # unknown / post-onboarding stage

    if idx == 0:
        return None  # already at the very first step

    # Step back
    previous_stage = _ONBOARDING_STAGE_ORDER[idx - 1]

    # Erase data that was collected at the stage we're leaving
    pending = session.setdefault("pending_data", {})
    for key in _CLEAR_ON_BACK_FROM.get(current_stage, []):
        pending.pop(key, None)

    # Special-case: language lives on the session root, not pending_data
    if current_stage == "SELECTING_LANGUAGE":
        session.pop("language", None)

    session["stage"] = previous_stage
    await save_session(whatsapp_no, session)

    return _STAGE_REPROMPT.get(
        previous_stage,
        f"You are back at step *{previous_stage.replace('_', ' ').title()}*.",
    )

HELP_TEXT = (
    "Here is what you can do:\n\n"
    "💰 *balance* — check your vault balances\n"
    "💸 *withdraw* — withdraw to your bank\n"
    "🏪 *pay* — pay a supplier\n"
    "📊 *summary* — get a business insight\n"
    "📈 *score* — view your trader score\n"
    "📋 *debrief* — get your daily report\n"
    "🆘 *help* — see this menu\n"
    "🙋 *human* — speak to a team member\n"
    "↩️ *back* — go back to the previous step (during setup)"
)


async def route_message(whatsapp_no: str, message: str):
    normalized_message = message.strip().lower()

    # ── Hard reset ─────────────────────────────────────────────────────────
    if normalized_message in RESET_COMMANDS:
        await clear_session(whatsapp_no)
        await clear_state_history(whatsapp_no)  # wipe undo stack on full reset
        session = await get_session(whatsapp_no)
        from app.agents.onboarding_agent import handle_onboarding

        await handle_onboarding(whatsapp_no, message, session)
        return

    # ── Revert state (back / undo) ───────────────────────────────────────────
    if normalized_message in BACK_COMMANDS:
        # Layer 1: try the Redis history stack (exact snapshots)
        previous = await pop_state_history(whatsapp_no)
        if previous is not None:
            restored_stage = previous.get("stage", "NEW")
            reprompt = _STAGE_REPROMPT.get(
                restored_stage,
                f"You are back at step *{restored_stage.replace('_', ' ').title()}*.",
            )
            await send_translated(whatsapp_no, reprompt, previous.get("language", "en"))
            return

        # Layer 2: stack is empty — synthesise a revert from the stage order.
        # This handles users who were already mid-onboarding before history
        # was introduced, or who have reached the bottom of the stack but
        # still want to keep going back.
        session = await get_session(whatsapp_no)
        reprompt = await _synthetic_back(whatsapp_no, session)
        if reprompt is not None:
            await send_translated(whatsapp_no, reprompt, session.get("language", "en"))
            return

        # Nothing left to revert to (e.g. already at SELECTING_LANGUAGE or ACTIVE)
        await send_translated(
            whatsapp_no,
            "↩️ You are already at the beginning — there is nothing further to go back to.\n\n"
            "Send *restart* to start completely over.",
            session.get("language", "en"),
        )
        return

    session = await get_session(whatsapp_no)

    # 1. Account locked
    if session.get("stage") == "LOCKED":
        await send_translated(
            whatsapp_no,
            "🔒 Your account is locked after too many wrong PIN attempts. "
            "A team member will contact you.",
            session.get("language", "en"),
        )
        return

    # 2. Escalated to human
    if session.get("stage") == "ESCALATED":
        await send_translated(
            whatsapp_no,
            "A team member is reviewing your case. Please wait — "
            "they will respond on this chat.",
            session.get("language", "en"),
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
