"""
Onboarding agent — guides new traders through AAJE setup via WhatsApp.

Flow:
  1. Language → 2. Name → 3. Location → 4. Business Type
  → 5. Account+Bank → 6. Mono Lookup → 7. Confirm Identity
  → 8. Connect Bank (CTA) → 9. Hustle Count → 10. Hustle Names
  → 11. Create Virtual Accounts → 12. Configure Splits
  → 13. Create PIN → 14. Confirm PIN → 15. Policy Acceptance
"""
import logging
import re
from urllib.parse import urlencode
import uuid

from app.config import settings
from sqlalchemy import insert

from app.database import AsyncSessionLocal
from app.models.income_stream import IncomeStream
from app.models.score import Score
from app.models.user import User
from app.models.vault import Vault
from app.redis import push_state_history, save_session, set_mono_pending, clear_state_history
from app.services.mono import BANK_CODES, lookup_account
from app.services.pin import hash_pin, is_valid_pin, verify_pin
from app.payments.squad import create_virtual_account, register_customer
from app.whatsapp.service import send_cta_button, send_text, send_translated
from app.services.whatsapp_flows import (
    BUSINESS_FLOW,
    PIN_SETUP_FLOW,
    PROFILE_FLOW,
    send_business_setup_flow,
    send_onboarding_profile_flow,
    send_pin_setup_flow,
)
from app.utils.formatters import format_naira, names_match, split_full_name

logger = logging.getLogger(__name__)


async def _tx(whatsapp_no: str, text: str, session: dict) -> None:
    """Translate-then-send shorthand for every onboarding stage handler."""
    await send_translated(whatsapp_no, text, session.get("language", "en"))

LANGUAGE_MAP = {
    "1": "yo", "yoruba": "yo",
    "2": "ig", "igbo": "ig",
    "3": "ha", "hausa": "ha",
    "4": "pcm", "pidgin": "pcm",
    "5": "en", "english": "en",
}

BUSINESS_TYPES = {
    "1": "Market Trader", "market trader": "Market Trader",
    "2": "Food Vendor", "food vendor": "Food Vendor",
    "3": "Shop Owner", "shop owner": "Shop Owner",
    "4": "Artisan", "artisan": "Artisan",
    "5": "Other", "other": "Other",
}


async def _send(whatsapp_no: str, text: str, language: str = "en"):
    """Translate *text* into the trader's language then send it.

    For English this is a no-op (translate_message returns text unchanged).
    For other languages one Groq call is made per message.
    The language selection screen is always sent in English directly
    (language not yet known), so call send_text directly there.
    """
    from app.intelligence.llm import translate_message
    translated = await translate_message(text, language)
    await send_text(whatsapp_no, translated)


async def handle_onboarding(whatsapp_no: str, message: str, session: dict):
    stage = session.get("stage", "NEW")
    session.setdefault("pending_data", {})

    handlers = {
        "NEW": _new,
        "SELECTING_LANGUAGE": _language,
        "AWAITING_PROFILE_FLOW": _awaiting_profile_flow,
        "COLLECTING_NAME": _name,
        "COLLECTING_LOCATION": _location,
        "COLLECTING_BUSINESS_TYPE": _business_type,
        "COLLECTING_ACCOUNT": _account,
        "CONFIRMING_IDENTITY": _confirm_identity,
        "CONNECTING_BANK": _connecting_bank,
        "AWAITING_BUSINESS_FLOW": _awaiting_business_flow,
        "COLLECTING_STREAM_COUNT": _stream_count,
        "COLLECTING_STREAM_NAMES": _stream_names,
        "CREATING_ACCOUNTS": _creating_accounts,
        "CONFIGURING_SPLITS": _configuring_splits,
        "AWAITING_PIN_SETUP_FLOW": _awaiting_pin_setup_flow,
        "CREATING_PIN": _create_pin,
        "CONFIRMING_PIN": _confirm_pin,
        "POLICY_ACCEPTANCE": _policy_acceptance,
    }
    handler = handlers.get(stage, _new)
    await handler(whatsapp_no, message, session)


async def handle_onboarding_flow(whatsapp_no: str, flow_response: dict, session: dict):
    session.setdefault("pending_data", {})
    flow_type = (session.get("pending_flow") or {}).get("type")
    data = flow_response.get("data") or {}

    if flow_type == PROFILE_FLOW:
        await _profile_flow_response(whatsapp_no, data, session)
        return
    if flow_type == BUSINESS_FLOW:
        await _business_flow_response(whatsapp_no, data, session)
        return
    if flow_type == PIN_SETUP_FLOW:
        await _pin_setup_flow_response(whatsapp_no, data, session)
        return

    await _tx(whatsapp_no, "I received that secure screen, but I was not expecting it. Please continue in chat.", session)


# ── Stage handlers ──────────────────────────────────────────────────

async def _new(whatsapp_no, _msg, session):
    await push_state_history(whatsapp_no, session)  # snapshot NEW before first step
    session["stage"] = "SELECTING_LANGUAGE"
    await save_session(whatsapp_no, session)
    await send_text(
        whatsapp_no,
        "Welcome to AAJE.\n\nChoose your language:\n1. Yoruba\n2. Igbo\n3. Hausa\n4. Pidgin\n5. English",
    )


async def _language(whatsapp_no, message, session):
    lang = LANGUAGE_MAP.get(message.lower().strip())
    if not lang:
        await send_text(whatsapp_no, "Please reply with 1, 2, 3, 4, or 5.")
        return
    await push_state_history(whatsapp_no, session)  # snapshot SELECTING_LANGUAGE
    session["language"] = lang
    session["stage"] = "AWAITING_PROFILE_FLOW"
    await save_session(whatsapp_no, session)
    sent = await send_onboarding_profile_flow(whatsapp_no, session)
    if sent:
        return
    session["stage"] = "COLLECTING_NAME"
    await save_session(whatsapp_no, session)
    await send_translated(whatsapp_no, "What is your full name?\nExample: Adebayo Olusegun Okonkwo", lang)


async def _awaiting_profile_flow(whatsapp_no, _message, session):
    sent = await send_onboarding_profile_flow(whatsapp_no, session)
    if sent:
        return
    session["stage"] = "COLLECTING_NAME"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "What is your full name?\nExample: Adebayo Olusegun Okonkwo", session)


async def _profile_flow_response(whatsapp_no, data: dict, session: dict):
    full_name = str(data.get("full_name") or data.get("name") or "").strip()
    location = str(data.get("location") or data.get("market") or "").strip()
    business_type = str(data.get("business_type") or "").strip()
    account_number = "".join(ch for ch in str(data.get("account_number") or "") if ch.isdigit())
    bank_name = str(data.get("bank_name") or data.get("bank") or "").strip()

    if len(full_name) < 2 or not location or not business_type:
        await _tx(whatsapp_no, "Please complete your name, market/town, and business type in the setup screen.", session)
        return
    if len(account_number) != 10 or not bank_name:
        await _tx(whatsapp_no, "Please enter a 10-digit account number and bank name in the setup screen.", session)
        return

    await push_state_history(whatsapp_no, session)
    pending = session["pending_data"]
    pending["full_name"] = full_name
    pending["location"] = location
    pending["business_type"] = business_type
    session["pending_flow"] = None
    session["stage"] = "COLLECTING_ACCOUNT"
    await save_session(whatsapp_no, session)
    await _account(whatsapp_no, f"{account_number} {bank_name}", session)


async def _name(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    if len(message.strip()) < 2:
        await _tx(whatsapp_no, "Please enter your full name (first, middle, last).\nExample: Adebayo Olusegun Okonkwo", session)
        return
    await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_NAME
    session["pending_data"]["full_name"] = message.strip()
    session["stage"] = "COLLECTING_LOCATION"
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, "What market or town do you trade in?", lang)


async def _location(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    session["pending_data"]["location"] = message.strip()
    session["stage"] = "COLLECTING_BUSINESS_TYPE"
    await save_session(whatsapp_no, session)
    await _send(
        whatsapp_no,
        "What type of business do you run?\n1. Market Trader\n2. Food Vendor\n3. Shop Owner\n4. Artisan\n5. Other",
        lang,
    )


async def _business_type(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    business_type = BUSINESS_TYPES.get(message.lower().strip())
    if not business_type:
        await _send(whatsapp_no, "Please reply with 1, 2, 3, 4, or 5.", lang)
        return
    await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_BUSINESS_TYPE
    session["pending_data"]["business_type"] = btype
    session["stage"] = "COLLECTING_ACCOUNT"
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, "Do you run more than one business? Reply 1 for Yes, 2 for No.", lang)

    # Mono lookup
    try:
        account_info = await lookup_account(
            account_number,
            bank_code,
            mock_account_name=session["pending_data"].get("full_name"),
        )
    except Exception:
        logger.exception("Mono lookup failed for %s", account_number)
        await _tx(whatsapp_no, "I could not verify that account right now. Please try again.", session)
        return

async def _stream_count(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    choice = message.strip().lower()
    if choice in {"1", "yes", "y"}:
        session["pending_data"]["stream_count"] = 2
        session["pending_data"]["streams"] = []
        session["stage"] = "COLLECTING_STREAM_NAMES"
        prompt = "Name your first business."
    elif choice in {"2", "no", "n"}:
        session["pending_data"]["stream_count"] = 1
        session["pending_data"]["streams"] = []
        session["stage"] = "COLLECTING_STREAM_NAMES"
        prompt = "What do you call your business? Give it a name you use yourself."
    else:
        await _send(whatsapp_no, "Reply 1 for Yes, 2 for No.", lang)
        return
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, prompt, lang)

    # Find the bank display name from code
    bank_display = next(
        (name.title() for name, code in BANK_CODES.items()
         if code == bank_code and len(name) > 3),
        "Unknown Bank",
    )

async def _stream_names(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    data = session["pending_data"]
    streams = data.setdefault("streams", [])
    streams.append({"stream_name": message.strip(), "is_savings": False, "is_emergency": False})
    if len(streams) < int(data.get("stream_count", 1)):
        await save_session(whatsapp_no, session)
        await _send(whatsapp_no, f"Name business {len(streams) + 1}.", lang)
        return
    session["stage"] = "COLLECTING_ACCOUNT"
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, "Enter the account number where customers send you money.", lang)


async def _account(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    account_number = message.replace(" ", "").strip()
    if not account_number.isdigit() or len(account_number) != 10:
        await _send(whatsapp_no, "Enter a valid 10-digit account number.", lang)
        return
    session["pending_data"]["account_number"] = account_number
    session["stage"] = "COLLECTING_BANK"
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, "What bank is this account with? e.g. GTBank, Access, Opay, Kuda", lang)


async def _bank(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    bank_code = BANK_CODES.get(message.lower().strip())
    if not bank_code:
        await _send(
            whatsapp_no,
            "I do not recognize that bank. Try GTBank, Access, Zenith, Opay, Kuda, or Moniepoint.",
            lang,
        )
        return

    # Mono lookup
    try:
        account_info = await lookup_account(
            account_number,
            bank_code,
            mock_account_name=session["pending_data"].get("full_name"),
        )
    except Exception:
        await _send(whatsapp_no, "I could not verify that account right now. Please try again.", lang)
        return

    verified_name = account_info.get("account_name") or account_info.get("name", "")
    if not verified_name:
        await _tx(whatsapp_no, "I could not find that account. Check the number and bank and try again.", session)
        return

    # Find the bank display name from code
    bank_display = next(
        (name.title() for name, code in BANK_CODES.items()
         if code == bank_code and len(name) > 3),
        "Unknown Bank",
    )

    data = session["pending_data"]
    try:
        account = await lookup_account(data["account_number"], bank_code)
    except Exception:
        await _send(whatsapp_no, "I could not verify that account right now. Please try again.", lang)
        return

    data = session["pending_data"]

    # Verify name match
    if not names_match(data["full_name"], data["verified_name"]):
        attempts = session.get("identity_attempts", 0) + 1
        session["identity_attempts"] = attempts
        if attempts >= 3:
            session["stage"] = "ESCALATED"
            await save_session(whatsapp_no, session)
            await _send(
                whatsapp_no,
                "We could not verify your identity after 3 attempts. A team member will contact you.",
                lang,
            )
            return
        session["stage"] = "COLLECTING_ACCOUNT"
        await save_session(whatsapp_no, session)
        await _send(whatsapp_no, "The account name does not match. Enter the account number again.", lang)
        return

    # Register Squad customer in background
    first, middle, last = split_full_name(data["full_name"])
    try:
        customer = await register_customer(
            first, middle, last, whatsapp_no, data["account_number"], data["bank_code"]
        )
        data["squad_customer_id"] = (
            customer.get("customer_id")
            or customer.get("id")
            or customer.get("customer_identifier")
        )
    except Exception:
        logger.exception("Squad customer registration failed")
        data["squad_customer_id"] = None

    data["verified_bank_account"] = data["account_number"]
    data["verified_bank_code"] = bank_code
    data["verified_bank_name"] = verified_name
    data["squad_customer_id"] = (
        customer.get("customer_id") or customer.get("id") or customer.get("customer_identifier")
    )
    session["stage"] = "CREATING_PIN"
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, f"Identity confirmed: {verified_name}. Now create a 4-digit PIN.", lang)


async def _create_pin(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    pin = message.strip()
    if not is_valid_pin(pin):
        await _send(whatsapp_no, "PIN must be exactly 4 digits and not obvious like 1234 or 1111.", lang)
        return

    await push_state_history(whatsapp_no, session)  # snapshot CONNECTING_BANK
    session["stage"] = "AWAITING_BUSINESS_FLOW"
    await save_session(whatsapp_no, session)
    sent = await send_business_setup_flow(whatsapp_no, session)
    if sent:
        return
    session["stage"] = "COLLECTING_STREAM_COUNT"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Do you run more than one business?\nReply 1 for Yes, 2 for No.", session)


async def _awaiting_business_flow(whatsapp_no, _message, session):
    sent = await send_business_setup_flow(whatsapp_no, session)
    if sent:
        return
    session["stage"] = "COLLECTING_STREAM_COUNT"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Do you run more than one business?\nReply 1 for Yes, 2 for No.", session)


async def _business_flow_response(whatsapp_no, data: dict, session: dict):
    num_businesses_str = str(data.get("num_businesses") or "1").strip()
    num_businesses = int(num_businesses_str) if num_businesses_str.isdigit() else 1
    
    b1 = str(data.get("business_1_name") or "").strip()
    b2 = str(data.get("business_2_name") or "").strip()
    b3 = str(data.get("business_3_name") or "").strip()
    
    include_savings = str(data.get("include_savings") or "").strip().lower() in {"yes", "true", "1"}
    include_emergency = str(data.get("include_emergency") or "").strip().lower() in {"yes", "true", "1"}

    if not b1:
        await _tx(whatsapp_no, "Please provide your first business name.", session)
        return

    streams = []
    streams.append({
        "stream_name": b1,
        "is_savings": False,
        "is_emergency": False,
    })
    
    if num_businesses >= 2 and b2:
        streams.append({
            "stream_name": b2,
            "is_savings": False,
            "is_emergency": False,
        })
        
    if num_businesses == 3 and b3:
        streams.append({
            "stream_name": b3,
            "is_savings": False,
            "is_emergency": False,
        })
        
    if include_savings:
        streams.append({
            "stream_name": "Savings",
            "is_savings": True,
            "is_emergency": False,
        })
        
    if include_emergency:
        streams.append({
            "stream_name": "Emergency",
            "is_savings": False,
            "is_emergency": True,
        })

    await push_state_history(whatsapp_no, session)
    session["pending_data"]["stream_count"] = len(streams)
    session["pending_data"]["streams"] = streams
    session["pending_flow"] = None
    session["stage"] = "CREATING_ACCOUNTS"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Creating your Squad accounts now...", session)
    await _creating_accounts(whatsapp_no, "", session)


async def _stream_count(whatsapp_no, message, session):
    choice = message.strip().lower()
    if choice in {"1", "yes", "y"}:
        await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_STREAM_COUNT
        session["pending_data"]["stream_count"] = 2
        session["pending_data"]["streams"] = []
        session["stage"] = "COLLECTING_STREAM_NAMES"
        prompt = "Name your first business."
    elif choice in {"2", "no", "n"}:
        await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_STREAM_COUNT
        session["pending_data"]["stream_count"] = 1
        session["pending_data"]["streams"] = []
        session["stage"] = "COLLECTING_STREAM_NAMES"
        prompt = "What do you call your business? Give it a name you use yourself."
    else:
        await _tx(whatsapp_no, "Reply 1 for Yes, 2 for No.", session)
        return
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, prompt, session)


async def _confirm_pin(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    if not verify_pin(message.strip(), session["pending_data"].get("pin_hash", "")):
        session["pending_data"].pop("pin_hash", None)
        session["stage"] = "CREATING_PIN"
        await save_session(whatsapp_no, session)
        await _send(whatsapp_no, "PINs do not match. Create your 4-digit PIN again.", lang)
        return

    # Automatically add savings and emergency vaults
    streams.append({"stream_name": "Savings", "is_savings": True, "is_emergency": False})
    streams.append({"stream_name": "Emergency", "is_savings": False, "is_emergency": True})

    session["stage"] = "CREATING_ACCOUNTS"
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, "PIN set. I am creating your Squad accounts now.", lang)
    await _creating_accounts(whatsapp_no, message, session)


async def _creating_accounts(whatsapp_no: str, _message: str, session: dict):
    lang = session.get("language", "en")
    data = session["pending_data"]
    customer_id = data.get("squad_customer_id")

    if not customer_id:
        # Retry Squad registration
        first, middle, last = split_full_name(data["full_name"])
        try:
            customer = await register_customer(
                first, middle, last, whatsapp_no, data["account_number"], data["bank_code"]
            )
            customer_id = (
                customer.get("customer_id")
                or customer.get("id")
                or customer.get("customer_identifier")
            )
            data["squad_customer_id"] = customer_id
        except Exception:
            logger.exception("Squad registration retry failed")
            await _tx(whatsapp_no, "Something went wrong setting up your accounts. Please try again in a moment.", session)
            return

    first, middle, last = split_full_name(data["full_name"])
    for i, stream in enumerate(data["streams"]):
        try:
            # Unique ID for each account to satisfy Squad reconciliation
            stream_id = f"{customer_id}-{i}"
            # Include stream name in last name so user can identify the account
            display_last = f"{last} ({stream['stream_name']})"

            account = await create_virtual_account(
                stream_id, first, middle, display_last, whatsapp_no, data["account_number"]
            )
            stream["squad_account_number"] = account.get("account_number") or account.get("virtual_account_number")
            stream["squad_account_id"] = account.get("account_id") or account.get("id")
            stream["squad_customer_id"] = stream_id
        except Exception:
            logger.exception("Virtual account creation failed for %s", stream["stream_name"])
            stream["squad_account_number"] = None
            stream["squad_account_id"] = None

    session["stage"] = "CONFIGURING_SPLITS"
    data["split_index"] = 0
    await save_session(whatsapp_no, session)
    await _send(whatsapp_no, f"What percentage should go to {data['streams'][0]['stream_name']}?", lang)


async def _configuring_splits(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    data = session["pending_data"]
    try:
        percentage = float(message.strip().replace("%", ""))
    except ValueError:
        await _send(whatsapp_no, "Enter the percentage as a number.", lang)
        return

    index = int(data.get("split_index", 0))
    data["streams"][index]["split_percentage"] = percentage
    index += 1
    data["split_index"] = index

    if index < len(data["streams"]):
        await save_session(whatsapp_no, session)
        await _send(whatsapp_no, f"What percentage should go to {data['streams'][index]['stream_name']}?", lang)
        return

    total = sum(float(s.get("split_percentage", 0)) for s in data["streams"])
    if round(total, 2) != 100:
        data["split_index"] = 0
        for s in data["streams"]:
            s.pop("split_percentage", None)
        await save_session(whatsapp_no, session)
        await _send(
            whatsapp_no,
            f"Those splits add up to {total}%. They must add up to 100%. Start again with {data['streams'][0]['stream_name']}.",
            lang,
        )
        return

    session["stage"] = "CREATING_PIN"
    await save_session(whatsapp_no, session)
    sent = await send_pin_setup_flow(whatsapp_no, session)
    if sent:
        session["stage"] = "AWAITING_PIN_SETUP_FLOW"
        await save_session(whatsapp_no, session)
        return
    await _tx(whatsapp_no, "Splits configured ✅\n\nNow create a 4-digit PIN to secure your account.", session)


async def _awaiting_pin_setup_flow(whatsapp_no, _message, session):
    sent = await send_pin_setup_flow(whatsapp_no, session)
    if sent:
        return
    session["stage"] = "CREATING_PIN"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Create a 4-digit PIN to secure your account.", session)


async def _pin_setup_flow_response(whatsapp_no, data: dict, session: dict):
    pin = str(data.get("pin") or data.get("new_pin") or "").strip()
    pin_confirm = str(data.get("pin_confirm") or data.get("confirm_pin") or "").strip()
    if not is_valid_pin(pin):
        await _tx(whatsapp_no, "PIN must be exactly 4 digits and not obvious like 1234 or 1111.", session)
        return
    if pin != pin_confirm:
        await _tx(whatsapp_no, "PINs do not match. Open the secure PIN screen and try again.", session)
        return

    await push_state_history(whatsapp_no, session)
    session["pending_data"]["pin_hash"] = hash_pin(pin)
    session["pending_flow"] = None
    session["stage"] = "POLICY_ACCEPTANCE"
    await save_session(whatsapp_no, session)
    await _tx(
        whatsapp_no,
        "AAJE Policy Summary\n\n"
        "- AAJE creates Squad virtual accounts for each of your businesses\n"
        "- Incoming payments are automatically split by your percentages\n"
        "- Withdrawals go only to your verified bank account\n"
        "- A N10 transaction fee applies on each deposit\n\n"
        "Reply *I Accept* to activate your account.",
        session,
    )


async def _create_pin(whatsapp_no, message, session):
    pin = message.strip()
    if not is_valid_pin(pin):
        await _tx(whatsapp_no, "PIN must be exactly 4 digits and not obvious like 1234 or 1111.", session)
        return
    session["pending_data"]["pin_hash"] = hash_pin(pin)
    session["stage"] = "CONFIRMING_PIN"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Confirm your PIN. Enter it again.", session)


async def _confirm_pin(whatsapp_no, message, session):
    if not verify_pin(message.strip(), session["pending_data"].get("pin_hash", "")):
        session["pending_data"].pop("pin_hash", None)
        session["stage"] = "CREATING_PIN"
        await save_session(whatsapp_no, session)
        await _tx(whatsapp_no, "PINs do not match. Create your 4-digit PIN again.", session)
        return
    session["stage"] = "POLICY_ACCEPTANCE"
    await save_session(whatsapp_no, session)
    await _send(
        whatsapp_no,
        (
            "Policy summary: AAJE creates Squad accounts, splits incoming money by your percentages, "
            "and withdrawals only go to your verified account. Reply I Accept to continue."
        ),
        lang,
    )


async def _policy_acceptance(whatsapp_no: str, message: str, session: dict):
    lang = session.get("language", "en")
    if message.lower().strip() not in {"i accept", "accept", "yes", "1"}:
        await _send(whatsapp_no, "Reply I Accept when you are ready.", lang)
        return

    data = session["pending_data"]
    user_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        await db.execute(
            insert(User).values(
                id=user_id,
                whatsapp_no=whatsapp_no,
                full_name=data["full_name"],
                location=data["location"],
                preferred_language=session.get("language", "en"),
                pin_hash=data["pin_hash"],
                verified_bank_account=data["verified_bank_account"],
                verified_bank_code=data["verified_bank_code"],
                verified_bank_name=data["verified_bank_name"],
                squad_customer_id=data["squad_customer_id"],
                onboarding_complete=True,
            )
        )
        for stream in data["streams"]:
            stream_id = uuid.uuid4()
            await db.execute(
                insert(IncomeStream).values(
                    id=stream_id,
                    user_id=user_id,
                    stream_name=stream["stream_name"],
                    stream_type=data.get("business_type"),
                    squad_account_id=stream.get("squad_account_id"),
                    squad_account_number=stream.get("squad_account_number"),
                    split_percentage=stream.get("split_percentage"),
                    is_savings=stream.get("is_savings", False),
                    is_emergency=stream.get("is_emergency", False),
                )
            )
            await db.execute(insert(Vault).values(user_id=user_id, stream_id=stream_id))
        await db.execute(insert(Score).values(
            user_id=user_id, credit_grade="D", recommended_loan_ceiling=0,
        ))
        await db.commit()

    session["onboarding_complete"] = True
    session["stage"] = "ACTIVE"
    session["pending_data"] = {}
    await save_session(whatsapp_no, session)
    await clear_state_history(whatsapp_no)  # onboarding done — no more "back"

    first, _, _ = split_full_name(data["full_name"])
    stream_summary = "\n".join(
        f"  • {s['stream_name']}: {s.get('split_percentage', 0)}%"
        for s in data["streams"]
    )
    await _tx(
        whatsapp_no,
        f"Welcome to AAJE, {first}. Your accounts are ready. Send balance anytime to check your money.",
        lang,
    )
