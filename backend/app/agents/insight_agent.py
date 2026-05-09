"""Insight agent — daily debrief and business analytics."""
import logging

from app.services import llm, notifier, refinery

logger = logging.getLogger(__name__)


async def handle(wa_number: str, body: str, session: dict) -> None:
    """Triggered by 'How am I doing?' / daily scheduler."""
    # TODO: fetch transactions from Postgres / Mono
    transactions = []  # placeholder
    context = refinery.full_context(transactions)
    insight_text = await llm.generate_insight(context)
    await notifier.send(wa_number, insight_text, voice=True)
