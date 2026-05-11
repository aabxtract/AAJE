from app.redis import save_session, set_mono_pending
from app.services.twilio_client import (
    send_text, send_buttons, send_cta_button
)
from app.services.mono import lookup_account, generate_connect_url
from app.services.squad import register_customer
from app.services.pin import hash_pin, is_valid_pin
from app.utils.formatters import names_match, split_full_name
from app.database import AsyncSessionLocal
from sqlalchemy import insert
from app.models.user import User
import uuid

BANK_CODES = {
    "gtbank": "058", "gtb": "058",
    "access": "044", "access bank": "044",
    "zenith": "057", "zenith bank": "057",
    "first bank": "011", "firstbank": "011",
    "uba": "033", "union bank": "032",
    "fidelity": "070", "sterling": "232",
    "wema": "035", "kuda": "090267",
    "opay": "100004", "palmpay": "100033",
    "moniepoint": "090405"
}

LANGUAGE_MAP = {
    "1": "yo", "yoruba": "yo",
    "2": "ig", "igbo": "ig",
    "3": "ha", "hausa": "ha",
    "4": "pcm", "pidgin": "pcm",
    "5": "en", "english": "en"
}

async def handle_onboarding(
    whatsapp_no: str,
    message: str,
    session: dict
):
    stage = session.get("stage", "NEW")

    if stage == "NEW":
        await _stage_language(whatsapp_no, session)

    elif stage == "SELECTING_LANGUAGE":
        await _handle_language(whatsapp_no, message, session)

    elif stage == "COLLECTING_NAME":
        await _handle_name(whatsapp_no, message, session)

    elif stage == "COLLECTING_LOCATION":
        await _handle_location(whatsapp_no, message, session)

    elif stage == "COLLECTING_BUSINESS_TYPE":
        await _handle_business_type(whatsapp_no, message, session)

    elif stage == "COLLECTING_HUSTLE_COUNT":
        await _handle_hustle_count(whatsapp_no, message, session)

    elif stage == "COLLECTING_HUSTLE_NAMES":
        await _handle_hustle_names(whatsapp_no, message, session)

    elif stage == "COLLECTING_ACCOUNT":
        await _handle_account_number(whatsapp_no, message, session)

    elif stage == "COLLECTING_BANK":
        await _handle_bank_name(whatsapp_no, message, session)

    elif stage == "VERIFYING_IDENTITY":
        await _handle_identity_confirmation(
            whatsapp_no, message, session
        )

    elif stage == "CREATING_PIN":
        await _handle_pin_creation(whatsapp_no, message, session)

    elif stage == "CONFIRMING_PIN":
        await _handle_pin_confirmation(whatsapp_no, message, session)

    elif stage == "AWAITING_MONO_CALLBACK":
        await send_text(
            whatsapp_no,
            "⏳ Still waiting for your bank connection. "
            "Please complete it in your browser."
        )

    elif stage == "SETTING_UP_VAULTS":
        from app.agents.vault_agent import handle_vault_setup
        await handle_vault_setup(whatsapp_no, message, session)

    elif stage == "CONFIGURING_SLICES":
        from app.agents.vault_agent import handle_slice_config
        await handle_slice_config(whatsapp_no, message, session)

    elif stage == "SETTING_DEBRIEF_TIME":
        await _handle_debrief_time(whatsapp_no, message, session)

    elif stage == "POLICY_ACCEPTANCE":
        await _handle_policy_acceptance(whatsapp_no, message, session)

# ── Stage handlers ──────────────────────────────────────────

async def _stage_language(whatsapp_no: str, session: dict):
    session["stage"] = "SELECTING_LANGUAGE"
    await save_session(whatsapp_no, session)
    await send_buttons(
        whatsapp_no,
        "👋 Welcome to AAJE — your Digital Business Manager.\n\n"
        "I will help you manage your money, track your sales, "
        "and grow your business.\n\n"
        "Choose your language:",
        ["Yoruba", "Igbo", "Hausa", "Pidgin", "English"]
    )

async def _handle_language(
    whatsapp_no: str, message: str, session: dict
):
    lang = LANGUAGE_MAP.get(message.lower().strip())
    if not lang:
        await send_text(
            whatsapp_no,
            "Please reply with a number:\n"
            "1. Yoruba\n2. Igbo\n3. Hausa\n4. Pidgin\n5. English"
        )
        return

    session["language"] = lang
    session["stage"] = "COLLECTING_NAME"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What is your full name?")

async def _handle_name(
    whatsapp_no: str, message: str, session: dict
):
    if len(message.strip()) < 2:
        await send_text(whatsapp_no, "Please enter your full name.")
        return

    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["full_name"] = message.strip()
    session["stage"] = "COLLECTING_LOCATION"
    await save_session(whatsapp_no, session)
    await send_text(
        whatsapp_no,
        "What market or town do you trade in?"
    )

async def _handle_location(
    whatsapp_no: str, message: str, session: dict
):
    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["location"] = message.strip()
    session["stage"] = "COLLECTING_BUSINESS_TYPE"
    await save_session(whatsapp_no, session)
    await send_buttons(
        whatsapp_no,
        "What type of business do you run?",
        ["Market Trader", "Food Vendor", "Shop Owner", "Other"]
    )

async def _handle_business_type(
    whatsapp_no: str, message: str, session: dict
):
    types = {
        "1": "market_trader", "market trader": "market_trader",
        "2": "food_vendor", "food vendor": "food_vendor",
        "3": "shop_owner", "shop owner": "shop_owner",
        "4": "other", "other": "other"
    }
    btype = types.get(message.lower().strip())
    if not btype:
        await send_text(
            whatsapp_no,
            "Please reply 1, 2, 3, or 4."
        )
        return

    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["business_type"] = btype
    session["stage"] = "COLLECTING_HUSTLE_COUNT"
    await save_session(whatsapp_no, session)
    await send_buttons(
        whatsapp_no,
        "Do you run more than one business?",
        ["Yes", "No"]
    )

async def _handle_hustle_count(
    whatsapp_no: str, message: str, session: dict
):
    is_multi = message.lower().strip() in ["yes", "1"]
    
    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["is_multi_hustle"] = is_multi
    
    if is_multi:
        session["stage"] = "COLLECTING_HUSTLE_NAMES"
        await save_session(whatsapp_no, session)
        await send_text(
            whatsapp_no,
            "Great! Please enter a name for each of your businesses, separated by a comma.\n"
            "Example: Adunola Provisions, Adunola Catering"
        )
    else:
        # Single stream: use business type as name
        btype_name = session["pending_data"].get("business_type", "Main Business").replace("_", " ").title()
        session["pending_data"]["hustle_names"] = [btype_name]
        session["stage"] = "COLLECTING_ACCOUNT"
        await save_session(whatsapp_no, session)
        await send_text(
            whatsapp_no,
            "Enter your POS account number\n"
            "(the account where customers send money to you):"
        )

async def _handle_hustle_names(
    whatsapp_no: str, message: str, session: dict
):
    names = [n.strip() for n in message.split(",") if n.strip()]
    if len(names) < 2:
        await send_text(whatsapp_no, "Please enter at least two business names separated by a comma.")
        return
        
    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["hustle_names"] = names
    session["stage"] = "COLLECTING_ACCOUNT"
    await save_session(whatsapp_no, session)
    await send_text(
        whatsapp_no,
        "Enter your POS account number\n"
        "(the account where customers send money to you):"
    )

async def _handle_account_number(
    whatsapp_no: str, message: str, session: dict
):
    account_no = message.strip().replace(" ", "")
    if not account_no.isdigit() or len(account_no) != 10:
        await send_text(
            whatsapp_no,
            "Please enter a valid 10-digit account number."
        )
        return

    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["account_number"] = account_no
    session["stage"] = "COLLECTING_BANK"
    await save_session(whatsapp_no, session)
    await send_text(
        whatsapp_no,
        "What is your bank name?\n"
        "(e.g. GTBank, Access Bank, Opay, Kuda, Moniepoint)"
    )

async def _handle_bank_name(
    whatsapp_no: str, message: str, session: dict
):
    bank_input = message.lower().strip()
    bank_code = BANK_CODES.get(bank_input)

    if not bank_code:
        await send_text(
            whatsapp_no,
            "I don't recognize that bank. "
            "Please try again.\n"
            "Examples: GTBank, Access Bank, Zenith, "
            "Opay, Kuda, Moniepoint"
        )
        return

    if "pending_data" not in session:
        session["pending_data"] = {}
        
    account_no = session["pending_data"].get("account_number")
    trader_name = session["pending_data"].get("full_name")

    try:
        result = await lookup_account(account_no, bank_code)
        bank_name_returned = result.get("name", "")

        if names_match(trader_name, bank_name_returned):
            # Identity confirmed
            session["pending_data"]["verified_bank_account"] = account_no
            session["pending_data"]["verified_bank_code"] = bank_code
            session["pending_data"]["verified_bank_name"] = message.strip()
            session["pending_data"]["verified_name"] = bank_name_returned
            session["stage"] = "CREATING_PIN"
            await save_session(whatsapp_no, session)

            await send_text(
                whatsapp_no,
                f"✅ Identity confirmed — {bank_name_returned}\n\n"
                f"Now create a 4-digit PIN.\n"
                f"You will use this PIN for all transfers.\n"
                f"Do not share it with anyone."
            )
        else:
            attempts = session.get("identity_attempts", 0) + 1
            session["identity_attempts"] = attempts

            if attempts >= 3:
                session["stage"] = "ESCALATED"
                await save_session(whatsapp_no, session)
                await send_text(
                    whatsapp_no,
                    "❌ We couldn't verify your identity after "
                    "3 attempts. A team member will contact you."
                )
                from app.agents.support_agent import trigger_escalation
                await trigger_escalation(
                    whatsapp_no,
                    "Identity verification failed 3 times",
                    "identity_failure",
                    session
                )
            else:
                session["stage"] = "COLLECTING_ACCOUNT"
                await save_session(whatsapp_no, session)
                await send_text(
                    whatsapp_no,
                    f"❌ The name on this account doesn't match "
                    f"what you gave us.\n"
                    f"Attempt {attempts}/3. "
                    f"Please check and try again.\n\n"
                    f"Enter your account number:"
                )

    except Exception:
        await send_text(
            whatsapp_no,
            "I couldn't reach the bank right now. "
            "Please try again in a moment."
        )

async def _handle_identity_confirmation(whatsapp_no: str, message: str, session: dict):
    # This function shouldn't normally be hit because the state immediately advances 
    # from COLLECTING_BANK to CREATING_PIN. Adding it as a safety net.
    pass

async def _handle_pin_creation(
    whatsapp_no: str, message: str, session: dict
):
    pin = message.strip()
    if not is_valid_pin(pin):
        await send_text(
            whatsapp_no,
            "❌ PIN must be exactly 4 digits.\n"
            "Avoid obvious PINs like 1234 or 1111.\n"
            "Try again:"
        )
        return

    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["pin_hash"] = hash_pin(pin)
    session["stage"] = "CONFIRMING_PIN"
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "Confirm your PIN — enter it again:")

async def _handle_pin_confirmation(
    whatsapp_no: str, message: str, session: dict
):
    from app.services.pin import verify_pin
    pin = message.strip()
    
    if "pending_data" not in session:
        session["pending_data"] = {}
        
    stored_hash = session["pending_data"].get("pin_hash")

    if verify_pin(pin, stored_hash):
        session["stage"] = "AWAITING_MONO_CALLBACK"
        user_id = str(uuid.uuid4())
        session["pending_data"]["user_id"] = user_id
        await save_session(whatsapp_no, session)
        await set_mono_pending(whatsapp_no)

        connect_url = await generate_connect_url(user_id)
        await send_cta_button(
            whatsapp_no,
            "✅ PIN set!\n\n"
            "Now let's connect your bank account so I can "
            "watch your transactions automatically.\n"
            "This takes about 2 minutes:",
            "Connect My Bank",
            connect_url
        )
    else:
        session["stage"] = "CREATING_PIN"
        session["pending_data"].pop("pin_hash", None)
        await save_session(whatsapp_no, session)
        await send_text(
            whatsapp_no,
            "❌ PINs don't match. Let's try again.\n"
            "Create your 4-digit PIN:"
        )

async def _handle_debrief_time(
    whatsapp_no: str, message: str, session: dict
):
    TIME_MAP = {
        "1": "19:00:00", "7pm": "19:00:00",
        "2": "20:00:00", "8pm": "20:00:00",
        "3": "21:00:00", "9pm": "21:00:00",
    }
    time_val = TIME_MAP.get(message.lower().strip(), "20:00:00")
    
    if "pending_data" not in session:
        session["pending_data"] = {}
        
    session["pending_data"]["daily_debrief_time"] = time_val
    session["stage"] = "POLICY_ACCEPTANCE"
    await save_session(whatsapp_no, session)

    await send_buttons(
        whatsapp_no,
        "📋 Almost done! Here's what you're agreeing to:\n\n"
        "✅ AAJE watches your linked account automatically\n"
        "✅ ₦5 is charged per automatic vault split\n"
        "✅ Withdrawals only go to your verified account\n"
        "✅ Your data is never sold to third parties\n"
        "✅ You can close your account anytime\n\n"
        "Do you accept?",
        ["I Accept", "Cancel"]
    )

async def _handle_policy_acceptance(
    whatsapp_no: str, message: str, session: dict
):
    if message.strip() not in ["1", "i accept", "accept", "yes"]:
        await send_text(
            whatsapp_no,
            "No problem. Reply 'I Accept' when you're ready."
        )
        return

    # Write everything to Postgres
    data = session.get("pending_data", {})
    first_name, last_name = split_full_name(data.get("full_name", "Trader"))

    async with AsyncSessionLocal() as db:
        user_id = data.get("user_id", str(uuid.uuid4()))
        from sqlalchemy.sql import func
        from app.models.hustle_stream import HustleStream
        
        await db.execute(
            insert(User).values(
                id=user_id,
                whatsapp_no=whatsapp_no,
                full_name=data.get("full_name", ""),
                location=data.get("location", ""),
                business_type=data.get("business_type", ""),
                preferred_language=session.get("language", "en"),
                pin_hash=data.get("pin_hash", ""),
                verified_bank_account=data.get("verified_bank_account", ""),
                verified_bank_code=data.get("verified_bank_code", ""),
                verified_bank_name=data.get("verified_bank_name", ""),
                mono_account_id=data.get("mono_account_id"),
                squad_customer_id=data.get("squad_customer_id"),
                daily_debrief_time=data.get("daily_debrief_time", "20:00:00"),
                onboarding_complete=True,
                policies_accepted_at=func.now()
            )
        )
        
        hustle_streams_to_insert = []
        for i, stream_name in enumerate(data.get("hustle_names", [])):
            squad_accounts = data.get(f"vaults_{i}", {})
            slice_config = data.get(f"slices_{i}", {})
            hustle_streams_to_insert.append({
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "stream_name": stream_name,
                "stream_type": data.get("business_type", ""),
                "squad_virtual_accounts": squad_accounts,
                "slice_config": slice_config,
                "is_primary": (i == 0)
            })
            
        if hustle_streams_to_insert:
            await db.execute(insert(HustleStream).values(hustle_streams_to_insert))
            
        await db.commit()

    session["onboarding_complete"] = True
    session["stage"] = "ACTIVE"
    session["pending_data"] = {}
    await save_session(whatsapp_no, session)

    debrief_time = data.get("daily_debrief_time", "20:00:00")[:5]
    await send_text(
        whatsapp_no,
        f"🎉 Welcome to AAJE, {first_name}!\n\n"
        f"I am now watching your account. "
        f"Every time money comes in, I will split it "
        f"into your vaults automatically.\n\n"
        f"You will get your first daily report at "
        f"{debrief_time}.\n\n"
        f"Just trade — I will handle the rest. 💪"
    )
