"""
Onboarding agent — drives the 6–8 step new trader registration flow.

Steps:
  1. greeting          → send welcome, ask for name
  2. collect_name      → store name, ask for account number + bank code
  3. verify_identity   → Mono lookup, name match (max 3 attempts)
  4. create_profile    → pass to Squad, create user record in Postgres
  5. setup_pin         → ask for 4-digit PIN
  6. confirm_pin       → confirm PIN, hash and store
  7. create_vaults     → create 3 Squad virtual accounts (operations/savings/emergency)
  8. complete          → welcome message, move state to ACTIVE
"""
import logging

from app import redis as r
from app.services import mono, notifier, squad, pin as pin_service
from app.utils.formatters import fmt_currency

logger = logging.getLogger(__name__)

MAX_IDENTITY_ATTEMPTS = 3

MESSAGES = {
    "greeting": (
        "👋 Welcome to AAJE — your personal business manager!\n\n"
        "AAJE helps you track sales, save automatically, and build your business history "
        "so you can access loans in the future.\n\n"
        "Let's get you set up. First — what is your full name?"
    ),
    "ask_account": (
        "Great, {name}! 💼\n\n"
        "Now enter your bank account number and bank code like this:\n"
        "Example: *0123456789 058*\n\n"
        "(Account number, space, then bank code)\n"
        "Your bank code is the 3-digit number used for transfers."
    ),
    "identity_fail": (
        "❌ The name on that account doesn't match what you gave us.\n"
        "Please check your account number and bank code and try again.\n"
        "Attempts left: {left}"
    ),
    "identity_locked": (
        "🔒 Too many failed attempts. Our team will review your registration "
        "and reach out to you within 24 hours."
    ),
    "identity_ok": (
        "✅ Identity confirmed! Welcome, {name}.\n\n"
        "Now set a 4-digit PIN to secure your AAJE account.\n"
        "Enter any 4 digits:"
    ),
    "confirm_pin": "Please enter your PIN one more time to confirm:",
    "pin_mismatch": "❌ PINs don't match. Let's try again. Enter your 4-digit PIN:",
    "setup_complete": (
        "🎉 You're all set, {name}!\n\n"
        "Your three savings vaults are ready:\n"
        "💰 Operations (60%) — daily working capital\n"
        "🏦 Savings (20%) — locked growth\n"
        "🛡️ Emergency (20%) — locked buffer\n\n"
        "Start by telling me how much you made today. "
        "Example: *I sold ₦18,000 today*"
    ),
}


async def handle(
    wa_number: str,
    body: str,
    media_url: str | None,
    session: dict,
) -> None:
    step = session.get("step", "greeting")

    if step == "greeting":
        await _do_greeting(wa_number, session)

    elif step == "collect_name":
        await _do_collect_name(wa_number, body, session)

    elif step == "verify_identity":
        await _do_verify_identity(wa_number, body, session)

    elif step == "setup_pin":
        await _do_setup_pin(wa_number, body, session)

    elif step == "confirm_pin":
        await _do_confirm_pin(wa_number, body, session)

    elif step == "create_vaults":
        await _do_create_vaults(wa_number, session)


# ── Step handlers ─────────────────────────────────────────────────────────────

async def _do_greeting(wa_number: str, session: dict) -> None:
    session.update({"state": "ONBOARDING", "step": "collect_name"})
    await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
    await notifier.send(wa_number, MESSAGES["greeting"])


async def _do_collect_name(wa_number: str, body: str, session: dict) -> None:
    name = body.strip().title()
    if len(name) < 2:
        await notifier.send(wa_number, "Please enter your full name.")
        return
    session.update({"step": "verify_identity", "name": name, "identity_attempts": 0})
    await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
    await notifier.send(wa_number, MESSAGES["ask_account"].format(name=name))


async def _do_verify_identity(wa_number: str, body: str, session: dict) -> None:
    parts = body.strip().split()
    if len(parts) != 2:
        await notifier.send(
            wa_number,
            "Please send your account number and bank code separated by a space.\nExample: *0123456789 058*",
        )
        return

    account_number, bank_code = parts[0], parts[1]
    attempts = session.get("identity_attempts", 0)
    trader_name = session.get("name", "")

    mono_name = await mono.lookup_account_name(account_number, bank_code)

    if mono_name and mono.names_match(trader_name, mono_name):
        session.update(
            {
                "step": "setup_pin",
                "account_number": account_number,
                "bank_code": bank_code,
                "verified_name": mono_name,
                "identity_attempts": 0,
            }
        )
        await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
        await notifier.send(
            wa_number, MESSAGES["identity_ok"].format(name=trader_name)
        )
    else:
        attempts += 1
        if attempts >= MAX_IDENTITY_ATTEMPTS:
            session.update({"state": "LOCKED", "step": "locked"})
            await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
            # TODO: write escalation record to Postgres
            await notifier.send(wa_number, MESSAGES["identity_locked"])
        else:
            session["identity_attempts"] = attempts
            await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
            await notifier.send(
                wa_number,
                MESSAGES["identity_fail"].format(left=MAX_IDENTITY_ATTEMPTS - attempts),
            )


async def _do_setup_pin(wa_number: str, body: str, session: dict) -> None:
    pin = body.strip()
    if not pin.isdigit() or len(pin) != 4:
        await notifier.send(wa_number, "PIN must be exactly 4 digits. Try again:")
        return
    session.update({"step": "confirm_pin", "pin_temp": pin})
    await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
    await notifier.send(wa_number, MESSAGES["confirm_pin"])


async def _do_confirm_pin(wa_number: str, body: str, session: dict) -> None:
    pin_confirm = body.strip()
    pin_temp = session.get("pin_temp", "")
    if pin_confirm != pin_temp:
        session.update({"step": "setup_pin", "pin_temp": None})
        await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
        await notifier.send(wa_number, MESSAGES["pin_mismatch"])
        return

    hashed = pin_service.hash_pin(pin_temp)
    session.update({"step": "create_vaults", "pin_hash": hashed, "pin_temp": None})
    await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
    await _do_create_vaults(wa_number, session)


async def _do_create_vaults(wa_number: str, session: dict) -> None:
    name = session.get("verified_name", session.get("name", "Trader"))
    first, *rest = name.split()
    last = " ".join(rest) if rest else first

    # TODO: Create 3 Squad virtual accounts and persist to Postgres
    # squad.create_virtual_account(...)

    session.update({"state": "ACTIVE", "step": "active"})
    await r.set_json(r.session_key(wa_number), session, r.SESSION_TTL)
    await notifier.send(
        wa_number,
        MESSAGES["setup_complete"].format(name=first),
        voice=True,
    )
