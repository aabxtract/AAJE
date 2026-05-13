from sqlalchemy import desc, select

from app.database import AsyncSessionLocal
from app.intelligence.llm import generate_insight, translate_message
from app.intelligence.refinery import compute_score
from app.models.income_stream import IncomeStream
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault
from app.services.whatsapp_client import send_text
from app.services.whatsapp_flows import send_passport_flow
from app.utils.formatters import format_naira
from app.utils.pii_scrubber import scrub


async def _user_for_whatsapp(db, whatsapp_no: str) -> User | None:
    result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
    return result.scalar_one_or_none()


async def handle_balance_check(whatsapp_no: str, session: dict):
    async with AsyncSessionLocal() as db:
        user = await _user_for_whatsapp(db, whatsapp_no)
        if not user:
            await send_text(whatsapp_no, "I could not find your AAJE account.")
            return
        result = await db.execute(
            select(IncomeStream, Vault)
            .join(Vault, Vault.stream_id == IncomeStream.id)
            .where(IncomeStream.user_id == user.id)
        )
        rows = result.all()

    if not rows:
        message = "No accounts found yet."
    else:
        lines = ["Your AAJE balances:"]
        for index, (stream, vault) in enumerate(rows, start=1):
            lines.append(f"{index}. {stream.stream_name}: {format_naira(vault.current_balance or 0)}")
        message = "\n".join(lines)

    message = await translate_message(message, session.get("language", "en"))
    await send_text(whatsapp_no, message)


async def handle_summary(whatsapp_no: str, session: dict):
    async with AsyncSessionLocal() as db:
        user = await _user_for_whatsapp(db, whatsapp_no)
        if not user:
            await send_text(whatsapp_no, "I could not find your AAJE account.")
            return
        score = await compute_score(str(user.id), db)
        tx_result = await db.execute(
            select(Transaction)
            .where(Transaction.user_id == user.id)
            .order_by(desc(Transaction.timestamp))
            .limit(30)
        )
        transactions = tx_result.scalars().all()

    context = scrub({
        "full_name": user.full_name,
        "score": score,
        "transactions": [
            {"amount": float(tx.amount), "type": tx.type, "category": tx.category}
            for tx in transactions
        ],
    })
    insight = await generate_insight(context)
    insight = await translate_message(insight, session.get("language", "en"))
    await send_text(whatsapp_no, insight)


async def handle_score(whatsapp_no: str, session: dict):
    async with AsyncSessionLocal() as db:
        user = await _user_for_whatsapp(db, whatsapp_no)
        if not user:
            await send_text(whatsapp_no, "I could not find your AAJE account.")
            return
        result = await db.execute(select(Score).where(Score.user_id == user.id))
        score = result.scalar_one_or_none()

    if not score:
        message = "Your score is not ready yet. Keep receiving verified payments to build it."
    else:
        sent = await send_passport_flow(
            whatsapp_no,
            session,
            {
                "full_name": user.full_name,
                "trader_score": float(score.trader_score or 0),
                "credit_grade": score.credit_grade or "D",
                "recommended_loan_ceiling": float(score.recommended_loan_ceiling or 0),
            },
        )
        if sent:
            return
        message = (
            f"Your AAJE score is {score.trader_score:.1f}, grade {score.credit_grade}. "
            f"Suggested credit threshold: {format_naira(score.recommended_loan_ceiling or 0)}."
        )
    message = await translate_message(message, session.get("language", "en"))
    await send_text(whatsapp_no, message)
