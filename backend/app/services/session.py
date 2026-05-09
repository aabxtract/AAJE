"""
Session router — the brain of AAJE.

Reads the current session state from Redis and dispatches
the inbound message to the correct agent.

State machine states:
  NEW              → onboarding_agent (step: greeting)
  ONBOARDING       → onboarding_agent
  ACTIVE           → intent classification → correct agent
  LOCKED           → support_agent (account locked)
"""
import logging

from app import redis as r
from app.agents import onboarding_agent, support_agent
from app.utils.message_parser import classify_intent

logger = logging.getLogger(__name__)


async def route_message(
    wa_number: str,
    body: str,
    media_url: str | None,
    media_content_type: str | None,
) -> None:
    session = await r.get_json(r.session_key(wa_number))

    if session is None:
        session = {"state": "NEW", "step": "greeting", "attempts": 0}

    state = session.get("state", "NEW")
    logger.info("Routing | %s | state=%s | body=%r", wa_number, state, body[:50])

    if state in ("NEW", "ONBOARDING"):
        await onboarding_agent.handle(wa_number, body, media_url, session)

    elif state == "LOCKED":
        await support_agent.handle(wa_number, body, session)

    elif state == "ACTIVE":
        intent = classify_intent(body)
        # Intent → agent dispatch (expanded in later sprints)
        logger.info("Intent: %s for %s", intent, wa_number)

    else:
        logger.warning("Unknown session state '%s' for %s", state, wa_number)
