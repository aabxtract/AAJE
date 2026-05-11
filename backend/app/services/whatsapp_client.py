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


async def send_text(to: str, message: str) -> dict:
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
