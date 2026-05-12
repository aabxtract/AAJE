"""
Support agent — handles frustrated users and explicit human-agent requests.
Escalations are logged to Postgres and the session is frozen until a team member resolves it.
"""
import logging

from sqlalchemy import insert, select

from app.database import AsyncSessionLocal
from app.models.escalation import Escalation
from app.models.user import User
from app.redis import save_session
from app.services.whatsapp_client import send_text
from app.utils.frustration import detect_frustration

logger = logging.getLogger(__name__)


async def handle_support(whatsapp_no: str, message: str, session: dict):
    """Tier-1 automated help.  If frustration or explicit human request is
    detected, escalate immediately; otherwise show the self-service menu."""
    if detect_frustration(message):
        await trigger_escalation(whatsapp_no, message, "frustration", session)
        return

    human_keywords = {"human", "person", "speak to someone", "real person", "agent", "talk to someone"}
    if any(kw in message.lower() for kw in human_keywords):
        await trigger_escalation(whatsapp_no, message, "explicit_request", session)
        return

    await send_text(
        whatsapp_no,
        "I can help you with:\n\n"
        "1. Check vault balances — reply *balance*\n"
        "2. Withdraw money — reply *withdraw*\n"
        "3. Pay a supplier — reply *pay*\n"
        "4. See your report — reply *summary*\n"
        "5. Speak to a person — reply *human*\n\n"
        "What do you need?",
    )


async def trigger_escalation(
    whatsapp_no: str,
    trigger_message: str,
    trigger_type: str,
    session: dict,
):
    """Create an escalation record and lock the session."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
        user = result.scalar_one_or_none()

        if user:
            snapshot = {
                "session_stage": session.get("stage"),
                "language": session.get("language"),
                "last_message": trigger_message,
            }
            await db.execute(
                insert(Escalation).values(
                    user_id=user.id,
                    trigger_message=trigger_message,
                    trigger_type=trigger_type,
                    conversation_snapshot=snapshot,
                    status="open",
                )
            )
            await db.commit()

    session["stage"] = "ESCALATED"
    await save_session(whatsapp_no, session)

    await send_text(
        whatsapp_no,
        "I'm connecting you to a team member right now. 🙏\n\n"
        "Someone will respond within 30 minutes.\n"
        "Please stay on this chat.",
    )
