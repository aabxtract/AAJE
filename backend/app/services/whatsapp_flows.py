import json
import logging
import secrets

from app.config import settings
from app.redis import save_flow_session, save_session
from app.services.whatsapp_client import send_cta_button, send_text

logger = logging.getLogger(__name__)

PROFILE_FLOW = "onboarding_profile"
BUSINESS_FLOW = "business_setup"
PIN_SETUP_FLOW = "pin_setup"
PIN_CONFIRM_FLOW = "pin_confirm"
PASSPORT_FLOW = "business_passport"

PROFILE_FLOW_DATA = {
    "business_types": [
        {"id": "Market Trader", "title": "Market Trader"},
        {"id": "Food Vendor", "title": "Food Vendor"},
        {"id": "Shop Owner", "title": "Shop Owner"},
        {"id": "Artisan", "title": "Artisan"},
        {"id": "Other", "title": "Other"},
    ]
}

BUSINESS_FLOW_DATA = {
    "yes_no": [
        {"id": "yes", "title": "Yes"},
        {"id": "no", "title": "No"},
    ]
}


def _with_flow_token(data: dict | None, token: str) -> dict:
    payload = dict(data or {})
    payload["flow_token"] = token
    return payload


def extract_flow_response(message: dict) -> dict | None:
    interactive = message.get("interactive") or {}
    if interactive.get("type") != "nfm_reply":
        return None

    reply = interactive.get("nfm_reply") or {}
    raw = reply.get("response_json") or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Invalid WhatsApp Flow response_json: %s", raw[:200])
        data = {}

    return {
        "name": reply.get("name"),
        "body": reply.get("body"),
        "flow_token": data.pop("flow_token", None),
        "data": data,
    }


async def _remember_flow(whatsapp_no: str, session: dict, flow_type: str) -> str:
    token = f"{flow_type}:{secrets.token_urlsafe(24)}"
    session["pending_flow"] = {"type": flow_type, "token": token}
    await save_session(whatsapp_no, session)
    return token


def _browser_flow_url(token: str) -> str:
    if not settings.app_public_url:
        return ""
    return f"{settings.app_public_url.rstrip('/')}/flow?token={token}"


async def _send_browser_flow(
    whatsapp_no: str,
    body: str,
    token: str,
    flow_type: str,
    cta: str,
    data: dict | None = None,
) -> bool:
    url = _browser_flow_url(token)
    if not url:
        logger.warning("APP_PUBLIC_URL is not configured; cannot send browser Flow link")
        return False
    payload = _with_flow_token(data, token)
    await save_flow_session(
        token,
        {
            "type": flow_type,
            "whatsapp_no": whatsapp_no,
            "data": payload,
        },
    )
    from app.intelligence.llm import translate_message
    from app.redis import get_session

    session = await get_session(whatsapp_no)
    language = session.get("language", "en")
    message = await translate_message(f"{body}\n\nOpen your secure AAJE screen here:", language)
    await send_cta_button(whatsapp_no, message, cta, url)
    return True


async def send_onboarding_profile_flow(whatsapp_no: str, session: dict) -> bool:
    token = await _remember_flow(whatsapp_no, session, PROFILE_FLOW)
    return await _send_browser_flow(
        whatsapp_no,
        "Open this secure AAJE setup screen to add your basic business details.",
        token,
        PROFILE_FLOW,
        "Start setup",
        PROFILE_FLOW_DATA,
    )


async def send_business_setup_flow(whatsapp_no: str, session: dict) -> bool:
    token = await _remember_flow(whatsapp_no, session, BUSINESS_FLOW)
    return await _send_browser_flow(
        whatsapp_no,
        "Set up your AAJE vaults and income split in one secure screen.",
        token,
        BUSINESS_FLOW,
        "Set vaults",
        BUSINESS_FLOW_DATA,
    )


async def send_pin_setup_flow(whatsapp_no: str, session: dict) -> bool:
    token = await _remember_flow(whatsapp_no, session, PIN_SETUP_FLOW)
    return await _send_browser_flow(
        whatsapp_no,
        "Create your private AAJE PIN in WhatsApp's secure form.",
        token,
        PIN_SETUP_FLOW,
        "Create PIN",
    )


async def send_pin_confirm_flow(whatsapp_no: str, session: dict, action_label: str) -> bool:
    token = await _remember_flow(whatsapp_no, session, PIN_CONFIRM_FLOW)
    return await _send_browser_flow(
        whatsapp_no,
        f"Enter your AAJE PIN securely to confirm {action_label}.",
        token,
        PIN_CONFIRM_FLOW,
        "Enter PIN",
        {"action_label": action_label},
    )


async def send_passport_flow(whatsapp_no: str, session: dict, passport_data: dict) -> bool:
    token = await _remember_flow(whatsapp_no, session, PASSPORT_FLOW)
    flow_data = {
        "full_name": str(passport_data.get("full_name") or ""),
        "trader_score": str(passport_data.get("trader_score") or "0"),
        "credit_grade": str(passport_data.get("credit_grade") or "D"),
        "recommended_loan_ceiling": str(passport_data.get("recommended_loan_ceiling") or "0"),
    }
    return await _send_browser_flow(
        whatsapp_no,
        "Your AAJE Business Passport is ready.",
        token,
        PASSPORT_FLOW,
        "View passport",
        flow_data,
    )


async def notify_flow_not_ready(whatsapp_no: str) -> None:
    await send_text(whatsapp_no, "That secure screen is not ready yet. Please continue in chat.")
