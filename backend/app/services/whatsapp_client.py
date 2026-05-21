import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_BASE = "https://graph.facebook.com/{version}/{phone_id}/messages"


def _url() -> str:
    return _BASE.format(
        version=settings.meta_graph_api_version,
        phone_id=settings.meta_phone_number_id,
    )


def _headers() -> dict:
    if not settings.meta_whatsapp_token:
        raise RuntimeError("META_WHATSAPP_TOKEN is not set")
    return {
        "Authorization": f"Bearer {settings.meta_whatsapp_token}",
        "Content-Type": "application/json",
    }


async def _post(payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(_url(), headers=_headers(), json=payload)
        if resp.status_code != 200:
            logger.error("WhatsApp API %s: %s", resp.status_code, resp.text[:500])
        return resp.json()


async def send_text(to: str, message: str) -> dict:
    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message},
    })


async def send_buttons(to: str, body: str, buttons: list[dict]) -> dict:
    rows = [{"id": str(b.get("id", i)), "title": b["title"][:24]} for i, b in enumerate(buttons[:10])]
    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": body},
            "action": {
                "button": "Choose",
                "sections": [{"title": "Options", "rows": rows}],
            },
        },
    })


async def send_cta_button(to: str, body: str, label: str, url: str) -> dict:
    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {"text": body},
            "action": {"name": "cta_url", "parameters": {"display_text": label, "url": url}},
        },
    })


async def send_image(to: str, image_url: str, caption: str = "") -> dict:
    return await _post({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "image",
        "image": {"link": image_url, "caption": caption},
    })
