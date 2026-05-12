from app.services.whatsapp_client import send_text
from app.utils.frustration import detect_frustration
from app.redis import save_session, get_session
from app.database import AsyncSessionLocal
from sqlalchemy import select, insert
from app.models.user import User
from app.models.escalation import Escalation

async def handle_support(
    whatsapp_no: str,
    message: str,
    session: dict
):
    language = session.get("language", "en")

    # Check for frustration
    if detect_frustration(message, language):
        await trigger_escalation(
            whatsapp_no,
            message,
            "frustration",
            session
        )
        return

    # Check explicit human request
    if any(word in message.lower() for word in [
        "human", "person", "speak to someone", "real person"
    ]):
        await trigger_escalation(
            whatsapp_no,
            message,
            "explicit_request",
            session
        )
        return

    # Tier-1 automated help
    await send_text(
        whatsapp_no,
        "I can help you with:\n\n"
        "1. Check vault balances — reply *balance*\n"
        "2. Withdraw money — reply *withdraw*\n"
        "3. Pay a supplier — reply *pay*\n"
        "4. See your report — reply *summary*\n"
        "5. Speak to a person — reply *human*\n\n"
        "What do you need?"
    )

async def trigger_escalation(
    whatsapp_no: str,
    trigger_message: str,
    trigger_type: str,
    session: dict
):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(User).where(User.whatsapp_no == whatsapp_no)
        )
        user = result.scalar_one_or_none()

        # Save conversation snapshot
        snapshot = {
            "session": session,
            "last_message": trigger_message
        }

        if user:
            await db.execute(
                insert(Escalation).values(
                    user_id=user.id,
                    trigger_message=trigger_message,
                    trigger_type=trigger_type,
                    conversation_snapshot=snapshot,
                    status="open"
                )
            )
            await db.commit()

    session["stage"] = "ESCALATED"
    await save_session(whatsapp_no, session)

    await send_text(
        whatsapp_no,
        "I'm connecting you to a team member right now. 🙏\n\n"
        "Someone will respond within 30 minutes.\n"
        "Please stay on this chat."
    )
