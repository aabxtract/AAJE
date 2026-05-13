import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def _url() -> str:
    return (
        f"https://graph.facebook.com/{settings.meta_graph_api_version}/"
        f"{settings.meta_phone_number_id}/messages"
    )


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.meta_whatsapp_token}",
        "Content-Type": "application/json",
    }


async def _post(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(_url(), headers=_headers(), json=payload)
    if response.status_code >= 300:
        logger.error("Meta WhatsApp API error %s: %s", response.status_code, response.text)
    response.raise_for_status()
    return response.json()


async def send_translated(to: str, message: str, language: str = "en") -> dict:
    """
    Translate ``message`` into the user's chosen language via the LLM,
    then send it.  Falls back to raw English if translation fails, returns empty,
    or is not needed (language == 'en').
    """
    from app.intelligence.llm import translate_message  # lazy import avoids circular deps
    translated = await translate_message(message, language)
    # Fallback to original message if translation failed or returned empty
    final_message = translated if (translated and translated.strip()) else message
    return await send_text(to, final_message)


async def send_text(to: str, message: str) -> dict:
    if not message or not message.strip():
        logger.warning("Attempted to send empty text to %s, skipping", to)
        return {"status": "skipped_empty"}
    
    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"preview_url": False, "body": message},
    })


async def send_buttons(to: str, body: str, buttons: list[str]) -> dict:
    options = "\n".join(f"{index + 1}. {label}" for index, label in enumerate(buttons))
    return await send_text(to, f"{body}\n\n{options}")


async def send_cta_button(to: str, body: str, button_label: str, url: str) -> dict:
    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body},
            "action": {
                "name": "cta_url",
                "parameters": {"display_text": button_label, "url": url},
            },
        },
    })


async def send_flow(
    to: str,
    body: str,
    flow_id: str,
    flow_token: str,
    cta: str,
    screen: str = "START",
    data: dict | None = None,
) -> dict:
    payload = {"screen": screen}
    if data:
        payload["data"] = data

    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "flow",
            "body": {"text": body},
            "action": {
                "name": "flow",
                "parameters": {
                    "mode": "published",
                    "flow_message_version": "3",
                    "flow_id": flow_id,
                    "flow_token": flow_token,
                    "flow_cta": cta,
                    "flow_action": "navigate",
                    "flow_action_payload": payload,
                },
            },
        },
    })
