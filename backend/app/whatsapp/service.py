"""
Legacy whatsapp service module — kept as a thin shim over
``app.services.whatsapp_client`` (Twilio for MVP).

Older code paths import from ``app.whatsapp.service`` directly. To keep
them working without touching every callsite during the Twilio swap, this
module re-exports the canonical client functions. New code should import
from ``app.services.whatsapp_client``.

Meta-specific features (Flows, native CTA buttons, list messages) are
intentionally degraded to plain text for MVP. They return when the Meta
migration lands in June 2026 (CLAUDE.md §20).
"""
from __future__ import annotations

import logging
from typing import Iterable

from app.services.whatsapp_client import (
    send_image,
    send_text,
)
from app.services.whatsapp_client import send_cta_link as _send_cta_link

logger = logging.getLogger(__name__)


async def send_translated(to: str, message: str, language: str = "en") -> dict:
    """Translate ``message`` into the user's chosen language via the LLM,
    then send it. Falls back to the original message on translation failure
    or when ``language == 'en'``."""
    from app.intelligence.llm import translate_message  # lazy import

    translated = await translate_message(message, language)
    final = translated if (translated and translated.strip()) else message
    return await send_text(to, final)


async def send_buttons(to: str, body: str, buttons: Iterable[str]) -> dict:
    """Plain-text numbered list (MVP). Real interactive list messages
    return when Meta WABA migration lands in June 2026."""
    options = "\n".join(f"{i + 1}. {label}" for i, label in enumerate(buttons))
    return await send_text(to, f"{body}\n\n{options}")


async def send_cta_button(to: str, body: str, button_label: str, url: str) -> dict:
    """Alias for :func:`send_cta_link`. Kept for legacy callers."""
    return await _send_cta_link(to, body, button_label, url)


async def send_flow(
    to: str,
    body: str,
    flow_id: str,
    flow_token: str,
    cta: str,
    screen: str = "START",
    data: dict | None = None,
) -> dict:
    """Meta WhatsApp Flows are not supported on Twilio.

    For MVP we log and degrade to a plain text message pointing at a
    hosted equivalent. The full Flow experience returns alongside the
    June 2026 Meta migration.
    """
    logger.warning(
        "send_flow called for flow %s but Flows are disabled in MVP (Twilio). "
        "Sending plain-text fallback.",
        flow_id,
    )
    return await send_text(to, body)


__all__ = [
    "send_text",
    "send_image",
    "send_translated",
    "send_buttons",
    "send_cta_button",
    "send_flow",
]
