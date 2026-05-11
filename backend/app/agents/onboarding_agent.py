import uuid

from sqlalchemy import insert

from app.database import AsyncSessionLocal
from app.models.income_stream import IncomeStream
from app.models.score import Score
from app.models.user import User
from app.models.vault import Vault
from app.redis import save_session
from app.services.mono import BANK_CODES, lookup_account
from app.services.pin import hash_pin, is_valid_pin, verify_pin
from app.services.squad import create_virtual_account, register_customer
from app.services.whatsapp_client import send_text
from app.utils.formatters import names_match, split_full_name

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


async def handle_onboarding(whatsapp_no: str, message: str, session: dict):
    stage = session.get("stage", "NEW")
    session.setdefault("pending_data", {})

    handlers = {
        "NEW": _new,
        "SELECTING_LANGUAGE": _language,
        "COLLECTING_NAME": _name,
        "COLLECTING_LOCATION": _location,
        "COLLECTING_BUSINESS_TYPE": _business_type,
        "COLLECTING_STREAM_COUNT": _stream_count,
        "COLLECTING_STREAM_NAMES": _stream_names,
        "COLLECTING_ACCOUNT": _account,
        "COLLECTING_BANK": _bank,
        "CREATING_PIN": _create_pin,
        "CONFIRMING_PIN": _confirm_pin,
        "CREATING_ACCOUNTS": _creating_accounts,
        "CONFIGURING_SPLITS": _configuring_splits,
        "POLICY_ACCEPTANCE": _policy_acceptance,
    }
    await handlers.get(stage, _new)(whatsapp_no, message, session)


async def _new(whatsapp_no: str, _message: str, session: dict):
    session["stage"] = "SELECTING_LANGUAGE"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "Welcome to AAJE. Choose your language:\n1. Yoruba\n2. Igbo\n3. Hausa\n4. Pidgin\n5. English")


async def _language(whatsapp_no: str, message: str, session: dict):
    language = LANGUAGE_MAP.get(message.lower().strip())
    if not language:
        await send_text(whatsapp_no, "Please reply with 1, 2, 3, 4, or 5.")
        return
    session["language"] = language
    session["stage"] = "COLLECTING_NAME"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What is your full name?")


async def _name(whatsapp_no: str, message: str, session: dict):
    if len(message.strip()) < 2:
        await send_text(whatsapp_no, "Please enter your full name.")
        return
    session["pending_data"]["full_name"] = message.strip()
    session["stage"] = "COLLECTING_LOCATION"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What market or town do you trade in?")


async def _location(whatsapp_no: str, message: str, session: dict):
    session["pending_data"]["location"] = message.strip()
    session["stage"] = "COLLECTING_BUSINESS_TYPE"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What type of business do you run?\n1. Market Trader\n2. Food Vendor\n3. Shop Owner\n4. Artisan\n5. Other")


async def _business_type(whatsapp_no: str, message: str, session: dict):
    business_type = BUSINESS_TYPES.get(message.lower().strip())
    if not business_type:
        await send_text(whatsapp_no, "Please reply with 1, 2, 3, 4, or 5.")
        return
    session["pending_data"]["business_type"] = business_type
    session["stage"] = "COLLECTING_STREAM_COUNT"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "Do you run more than one business? Reply 1 for Yes, 2 for No.")


async def _stream_count(whatsapp_no: str, message: str, session: dict):
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
        await send_text(whatsapp_no, "Reply 1 for Yes, 2 for No.")
        return
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, prompt)


async def _stream_names(whatsapp_no: str, message: str, session: dict):
    data = session["pending_data"]
    streams = data.setdefault("streams", [])
    streams.append({"stream_name": message.strip(), "is_savings": False, "is_emergency": False})
    if len(streams) < int(data.get("stream_count", 1)):
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, f"Name business {len(streams) + 1}.")
        return
    session["stage"] = "COLLECTING_ACCOUNT"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "Enter the account number where customers send you money.")


async def _account(whatsapp_no: str, message: str, session: dict):
    account_number = message.replace(" ", "").strip()
    if not account_number.isdigit() or len(account_number) != 10:
        await send_text(whatsapp_no, "Enter a valid 10-digit account number.")
        return
    session["pending_data"]["account_number"] = account_number
    session["stage"] = "COLLECTING_BANK"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What bank is this account with? e.g. GTBank, Access, Opay, Kuda")


async def _bank(whatsapp_no: str, message: str, session: dict):
    bank_code = BANK_CODES.get(message.lower().strip())
    if not bank_code:
        await send_text(whatsapp_no, "I do not recognize that bank. Try GTBank, Access, Zenith, Opay, Kuda, or Moniepoint.")
        return
    data = session["pending_data"]
    try:
        account = await lookup_account(data["account_number"], bank_code)
    except Exception:
        await send_text(whatsapp_no, "I could not verify that account right now. Please try again.")
        return
    verified_name = account.get("account_name") or account.get("name", "")
    if not names_match(data["full_name"], verified_name):
        attempts = session.get("identity_attempts", 0) + 1
        session["identity_attempts"] = attempts
        if attempts >= 3:
            session["stage"] = "ESCALATED"
            await save_session(whatsapp_no, session)
            await send_text(whatsapp_no, "We could not verify your identity after 3 attempts. A team member will contact you.")
            return
        session["stage"] = "COLLECTING_ACCOUNT"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, "The account name does not match. Enter the account number again.")
        return
    first, last = split_full_name(data["full_name"])
    customer = await register_customer(first, last, whatsapp_no, data["account_number"], bank_code)
    data["verified_bank_account"] = data["account_number"]
    data["verified_bank_code"] = bank_code
    data["verified_bank_name"] = verified_name
    data["squad_customer_id"] = customer.get("customer_id") or customer.get("id") or customer.get("customer_identifier")
    session["stage"] = "CREATING_PIN"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, f"Identity confirmed: {verified_name}. Now create a 4-digit PIN.")


async def _create_pin(whatsapp_no: str, message: str, session: dict):
    pin = message.strip()
    if not is_valid_pin(pin):
        await send_text(whatsapp_no, "PIN must be exactly 4 digits and not obvious like 1234 or 1111.")
        return
    session["pending_data"]["pin_hash"] = hash_pin(pin)
    session["stage"] = "CONFIRMING_PIN"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "Confirm your PIN. Enter it again.")


async def _confirm_pin(whatsapp_no: str, message: str, session: dict):
    if not verify_pin(message.strip(), session["pending_data"].get("pin_hash", "")):
        session["pending_data"].pop("pin_hash", None)
        session["stage"] = "CREATING_PIN"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, "PINs do not match. Create your 4-digit PIN again.")
        return
    session["stage"] = "CREATING_ACCOUNTS"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "PIN set. I am creating your Squad accounts now.")
    await _creating_accounts(whatsapp_no, message, session)


async def _creating_accounts(whatsapp_no: str, _message: str, session: dict):
    data = session["pending_data"]
    for stream in data["streams"]:
        account = await create_virtual_account(data["squad_customer_id"], stream["stream_name"])
        stream["squad_account_number"] = account.get("account_number") or account.get("virtual_account_number")
        stream["squad_account_id"] = account.get("account_id") or account.get("id")
    session["stage"] = "CONFIGURING_SPLITS"
    session["pending_data"]["split_index"] = 0
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, f"What percentage should go to {data['streams'][0]['stream_name']}?")


async def _configuring_splits(whatsapp_no: str, message: str, session: dict):
    data = session["pending_data"]
    try:
        percentage = float(message.strip().replace("%", ""))
    except ValueError:
        await send_text(whatsapp_no, "Enter the percentage as a number.")
        return
    index = int(data.get("split_index", 0))
    data["streams"][index]["split_percentage"] = percentage
    index += 1
    data["split_index"] = index
    if index < len(data["streams"]):
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, f"What percentage should go to {data['streams'][index]['stream_name']}?")
        return
    total = sum(float(stream.get("split_percentage", 0)) for stream in data["streams"])
    if round(total, 2) != 100:
        data["split_index"] = 0
        for stream in data["streams"]:
            stream.pop("split_percentage", None)
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, f"Those splits add up to {total}%. They must add up to 100%. Start again with {data['streams'][0]['stream_name']}.")
        return
    session["stage"] = "POLICY_ACCEPTANCE"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "Policy summary: AAJE creates Squad accounts, splits incoming money by your percentages, and withdrawals only go to your verified account. Reply I Accept to continue.")


async def _policy_acceptance(whatsapp_no: str, message: str, session: dict):
    if message.lower().strip() not in {"i accept", "accept", "yes", "1"}:
        await send_text(whatsapp_no, "Reply I Accept when you are ready.")
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
            squad_customer_id=data["squad_customer_id"],
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
        await db.execute(insert(Score).values(user_id=user_id, credit_grade="D", recommended_loan_ceiling=0))
        await db.commit()

    session["onboarding_complete"] = True
    session["stage"] = "ACTIVE"
    session["pending_data"] = {}
    await save_session(whatsapp_no, session)
    first, _ = split_full_name(data["full_name"])
    await send_text(whatsapp_no, f"Welcome to AAJE, {first}. Your accounts are ready. Send balance anytime to check your money.")
