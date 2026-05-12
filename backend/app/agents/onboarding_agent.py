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
from app.services.squad import create_virtual_account, register_customer
from app.services.whatsapp_client import send_cta_button, send_text, send_translated
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


def _parse_account_and_bank(message: str):
    """Parse '0123456789 GTBank' into (account_number, bank_code)."""
    msg = message.strip()
    # Extract 10-digit account number
    match = re.search(r"\b(\d{10})\b", msg)
    if not match:
        return None, None
    account_number = match.group(1)
    # Remove the account number to find the bank name
    remaining = msg.replace(account_number, "").strip().strip(",").strip()
    bank_code = BANK_CODES.get(remaining.lower())
    return account_number, bank_code


def _mono_connect_url(whatsapp_no: str) -> str:
    if settings.mono_lookup_mock and settings.app_public_url:
        public_url = settings.app_public_url.rstrip("/")
        return f"{public_url}/mono/mock-connect?{urlencode({'reference': whatsapp_no})}"

    params = {
        "key": settings.mono_public_key,
        "reference": whatsapp_no,
    }
    if settings.app_public_url:
        public_url = settings.app_public_url.rstrip("/")
        params["redirect_url"] = f"{public_url}/mono/return"
    return f"https://connect.mono.co/?{urlencode(params)}"


async def handle_onboarding(whatsapp_no: str, message: str, session: dict):
    stage = session.get("stage", "NEW")
    session.setdefault("pending_data", {})

    handlers = {
        "NEW": _new,
        "SELECTING_LANGUAGE": _language,
        "COLLECTING_NAME": _name,
        "COLLECTING_LOCATION": _location,
        "COLLECTING_BUSINESS_TYPE": _business_type,
        "COLLECTING_ACCOUNT": _account,
        "CONFIRMING_IDENTITY": _confirm_identity,
        "CONNECTING_BANK": _connecting_bank,
        "COLLECTING_STREAM_COUNT": _stream_count,
        "COLLECTING_STREAM_NAMES": _stream_names,
        "CREATING_ACCOUNTS": _creating_accounts,
        "CONFIGURING_SPLITS": _configuring_splits,
        "CREATING_PIN": _create_pin,
        "CONFIRMING_PIN": _confirm_pin,
        "POLICY_ACCEPTANCE": _policy_acceptance,
    }
    handler = handlers.get(stage, _new)
    await handler(whatsapp_no, message, session)


# ── Stage handlers ──────────────────────────────────────────────────

async def _new(whatsapp_no, _msg, session):
    await push_state_history(whatsapp_no, session)  # snapshot NEW before first step
    session["stage"] = "SELECTING_LANGUAGE"
    await save_session(whatsapp_no, session)
    await send_text(
        whatsapp_no,
        "Welcome to AAJE 🇳🇬\nYour Digital Business Manager.\n\n"
        "Choose your language:\n1. Yoruba\n2. Igbo\n3. Hausa\n4. Pidgin\n5. English",
    )


async def _language(whatsapp_no, message, session):
    lang = LANGUAGE_MAP.get(message.lower().strip())
    if not lang:
        await send_text(whatsapp_no, "Please reply with 1, 2, 3, 4, or 5.")
        return
    await push_state_history(whatsapp_no, session)  # snapshot SELECTING_LANGUAGE
    session["language"] = lang
    session["stage"] = "COLLECTING_NAME"
    await save_session(whatsapp_no, session)
    await send_translated(whatsapp_no, "What is your full name?\nExample: Adebayo Olusegun Okonkwo", lang)


async def _name(whatsapp_no, message, session):
    if len(message.strip()) < 2:
        await _tx(whatsapp_no, "Please enter your full name (first, middle, last).\nExample: Adebayo Olusegun Okonkwo", session)
        return
    await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_NAME
    session["pending_data"]["full_name"] = message.strip()
    session["stage"] = "COLLECTING_LOCATION"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "What market or town do you trade in?", session)


async def _location(whatsapp_no, message, session):
    await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_LOCATION
    session["pending_data"]["location"] = message.strip()
    session["stage"] = "COLLECTING_BUSINESS_TYPE"
    await save_session(whatsapp_no, session)
    await _tx(
        whatsapp_no,
        "What type of business do you run?\n"
        "1. Market Trader\n2. Food Vendor\n3. Shop Owner\n4. Artisan\n5. Other",
        session,
    )


async def _business_type(whatsapp_no, message, session):
    btype = BUSINESS_TYPES.get(message.lower().strip())
    if not btype:
        await _tx(whatsapp_no, "Please reply with 1, 2, 3, 4, or 5.", session)
        return
    await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_BUSINESS_TYPE
    session["pending_data"]["business_type"] = btype
    session["stage"] = "COLLECTING_ACCOUNT"
    await save_session(whatsapp_no, session)
    await _tx(
        whatsapp_no,
        "Enter your account number and bank.\n"
        "Example: 0123456789 GTBank",
        session,
    )


async def _account(whatsapp_no, message, session):
    account_number, bank_code = _parse_account_and_bank(message)
    if not account_number:
        await _tx(whatsapp_no, "I could not find a 10-digit account number. Try again.\nExample: 0123456789 GTBank", session)
        return
    if not bank_code:
        await _tx(
            whatsapp_no,
            "I did not recognize the bank name. Try again with the full name.\n"
            "Example: 0123456789 GTBank\n\n"
            "Supported: GTBank, Access, Zenith, First Bank, UBA, Kuda, OPay, Moniepoint, PalmPay, Wema, Fidelity, Sterling, FCMB, Ecobank",
            session,
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
        logger.exception("Mono lookup failed for %s", account_number)
        await _tx(whatsapp_no, "I could not verify that account right now. Please try again.", session)
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
    await push_state_history(whatsapp_no, session)  # snapshot COLLECTING_ACCOUNT
    data["account_number"] = account_number
    data["bank_code"] = bank_code
    data["bank_display"] = bank_display
    data["verified_name"] = verified_name
    session["stage"] = "CONFIRMING_IDENTITY"
    await save_session(whatsapp_no, session)

    await _tx(
        whatsapp_no,
        f"✅ Account found!\n\n"
        f"*Name:* {verified_name}\n"
        f"*Account:* {account_number}\n"
        f"*Bank:* {bank_display}\n\n"
        "Is this correct? Reply *Yes* or *No*.",
        session,
    )


async def _confirm_identity(whatsapp_no, message, session):
    reply = message.lower().strip()
    if reply in {"no", "n", "2", "wrong"}:
        session["stage"] = "COLLECTING_ACCOUNT"
        await save_session(whatsapp_no, session)
        await _tx(whatsapp_no, "No problem. Enter your account number and bank again.\nExample: 0123456789 GTBank", session)
        return
    if reply not in {"yes", "y", "1", "correct", "confirm"}:
        await _tx(whatsapp_no, "Reply *Yes* or *No*.", session)
        return

    data = session["pending_data"]

    # Verify name match
    if not names_match(data["full_name"], data["verified_name"]):
        attempts = session.get("identity_attempts", 0) + 1
        session["identity_attempts"] = attempts
        if attempts >= 3:
            session["stage"] = "ESCALATED"
            await save_session(whatsapp_no, session)
            await _tx(whatsapp_no, "We could not verify your identity after 3 attempts. A team member will contact you.", session)
            return
        session["stage"] = "COLLECTING_ACCOUNT"
        await save_session(whatsapp_no, session)
        await _tx(whatsapp_no, "The account name does not match the name you gave. Please try a different account.\nExample: 0123456789 GTBank", session)
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
    data["verified_bank_code"] = data["bank_code"]
    data["verified_bank_name"] = data["verified_name"]

    await push_state_history(whatsapp_no, session)  # snapshot CONFIRMING_IDENTITY
    session["stage"] = "CONNECTING_BANK"
    await save_session(whatsapp_no, session)
    await set_mono_pending(whatsapp_no)

    # Send Mono Connect CTA button
    connect_url = _mono_connect_url(whatsapp_no)
    lang = session.get("language", "en")
    from app.intelligence.llm import translate_message
    cta_body = await translate_message(
        "Tap the button below to securely connect your bank for deeper insights and credit scoring.\n\nAfter connecting, reply *done* to continue. Or reply *skip* to continue without connecting.",
        lang,
    )
    await send_cta_button(whatsapp_no, cta_body, "Connect Bank 🔗", connect_url)


async def _connecting_bank(whatsapp_no, message, session):
    reply = message.lower().strip()
    if reply not in {"done", "skip", "continue", "next"}:
        await _tx(whatsapp_no, "Reply *done* after connecting your bank, or *skip* to continue without it.", session)
        return

    await push_state_history(whatsapp_no, session)  # snapshot CONNECTING_BANK
    session["stage"] = "COLLECTING_STREAM_COUNT"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Do you run more than one business?\nReply 1 for Yes, 2 for No.", session)


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


async def _stream_names(whatsapp_no, message, session):
    data = session["pending_data"]
    streams = data.setdefault("streams", [])
    streams.append({"stream_name": message.strip(), "is_savings": False, "is_emergency": False})
    if len(streams) < int(data.get("stream_count", 1)):
        await save_session(whatsapp_no, session)
        await _tx(whatsapp_no, f"Name business {len(streams) + 1}.", session)
        return

    # Automatically add savings and emergency vaults
    streams.append({"stream_name": "Savings", "is_savings": True, "is_emergency": False})
    streams.append({"stream_name": "Emergency", "is_savings": False, "is_emergency": True})

    session["stage"] = "CREATING_ACCOUNTS"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Creating your Squad accounts now... ⏳", session)
    await _creating_accounts(whatsapp_no, message, session)


async def _creating_accounts(whatsapp_no, _msg, session):
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
                stream_id, first, middle, display_last, whatsapp_no
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

    stream_list = "\n".join(
        f"  {i+1}. {s['stream_name']}" for i, s in enumerate(data["streams"])
    )
    await _tx(
        whatsapp_no,
        f"✅ Accounts created!\n\n{stream_list}\n\n"
        f"What percentage of your income should go to *{data['streams'][0]['stream_name']}*?\n"
        "All percentages must add up to 100%.",
        session,
    )


async def _configuring_splits(whatsapp_no, message, session):
    data = session["pending_data"]
    try:
        percentage = float(message.strip().replace("%", ""))
    except ValueError:
        await _tx(whatsapp_no, "Enter the percentage as a number. Example: 50", session)
        return

    index = int(data.get("split_index", 0))
    data["streams"][index]["split_percentage"] = percentage
    index += 1
    data["split_index"] = index

    if index < len(data["streams"]):
        await save_session(whatsapp_no, session)
        await _tx(whatsapp_no, f"What percentage should go to *{data['streams'][index]['stream_name']}*?", session)
        return

    total = sum(float(s.get("split_percentage", 0)) for s in data["streams"])
    if round(total, 2) != 100:
        data["split_index"] = 0
        for s in data["streams"]:
            s.pop("split_percentage", None)
        await save_session(whatsapp_no, session)
        await _tx(
            whatsapp_no,
            f"Those splits add up to {total}%. They must total 100%.\n"
            f"Start again — what percentage for *{data['streams'][0]['stream_name']}*?",
            session,
        )
        return

    session["stage"] = "CREATING_PIN"
    await save_session(whatsapp_no, session)
    await _tx(whatsapp_no, "Splits configured ✅\n\nNow create a 4-digit PIN to secure your account.", session)


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
    await _tx(
        whatsapp_no,
        "📋 *AAJE Policy Summary*\n\n"
        "• AAJE creates Squad virtual accounts for each of your businesses\n"
        "• Incoming payments are automatically split by your percentages\n"
        "• Withdrawals go only to your verified bank account\n"
        "• A ₦10 transaction fee applies on each deposit\n\n"
        "Reply *I Accept* to activate your account.",
        session,
    )


async def _policy_acceptance(whatsapp_no, message, session):
    if message.lower().strip() not in {"i accept", "accept", "yes", "1"}:
        await _tx(whatsapp_no, "Reply *I Accept* when you are ready.", session)
        return

    data = session["pending_data"]
    user_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        await db.execute(insert(User).values(
            id=user_id,
            whatsapp_no=whatsapp_no,
            full_name=data["full_name"],
            location=data["location"],
            preferred_language=session.get("language", "en"),
            pin_hash=data["pin_hash"],
            verified_bank_account=data["verified_bank_account"],
            verified_bank_code=data["verified_bank_code"],
            verified_bank_name=data["verified_bank_name"],
            squad_customer_id=data.get("squad_customer_id"),
            onboarding_complete=True,
        ))
        for stream in data["streams"]:
            stream_id = uuid.uuid4()
            await db.execute(insert(IncomeStream).values(
                id=stream_id,
                user_id=user_id,
                stream_name=stream["stream_name"],
                stream_type=data.get("business_type"),
                squad_account_id=stream.get("squad_account_id"),
                squad_account_number=stream.get("squad_account_number"),
                split_percentage=stream.get("split_percentage"),
                is_savings=stream.get("is_savings", False),
                is_emergency=stream.get("is_emergency", False),
            ))
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
        f"🎉 Welcome to AAJE, {first}!\n\n"
        f"Your accounts are ready:\n{stream_summary}\n\n"
        "Send *balance* anytime to check your money.\n"
        "Send *help* to see all commands.",
        session,
    )
