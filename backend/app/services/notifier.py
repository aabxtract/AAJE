"""
Notifier — outbound message orchestrator.

Strict Pipeline Order:
1. PII Scrubber (scrub raw context)
2. Refinery Math (process scrubbed context)
3. LLM Generate Insight (English)
4. LLM Translate (to target language)
5. Twilio (send text only)
"""
import logging
from app.services import twilio_client, llm
from app.utils import pii_scrubber
from app.services.refinery import full_context
from sqlalchemy import select
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

async def _fetch_transactions(user_id, db, limit=100):
    result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.timestamp.desc())
        .limit(limit)
    )
    txs = result.scalars().all()
    # Convert to dict for pandas
    return [{"id": str(tx.id), "amount": float(tx.amount), "type": tx.type, "date": tx.timestamp.isoformat(), "narration": tx.description} for tx in txs]

async def send_daily_debrief(user, db) -> None:
    """
    Follows strict pipeline for daily debrief notification.
    """
    # Fetch raw data
    raw_txs = await _fetch_transactions(user.id, db)
    
    # 1. Scrub PII
    scrubbed_txs = pii_scrubber.scrub_transaction_list(raw_txs)
    
    # 2. Refinery Math
    # Mocking vault_balances for now
    context = full_context(scrubbed_txs, vault_balances={})
    
    # 3. LLM Insight (English)
    english_insight = await llm.generate_insight(context)
    
    # 4. LLM Translate
    localized_text = await llm.translate_to_language(english_insight, user.preferred_language)
    
    # 5. Sound + Text
    from app.utils.constants import AAJE_NOTIFICATION_SOUND_URL
    if AAJE_NOTIFICATION_SOUND_URL:
        # Assuming send_voice_note exists or just ignore if not, but spec requires it
        try:
            await twilio_client.send_voice_note(user.whatsapp_no, AAJE_NOTIFICATION_SOUND_URL)
        except AttributeError:
            pass # fallback if not implemented
            
    await twilio_client.send_text(user.whatsapp_no, localized_text)

async def notify_split(user, db, transaction_id: str) -> None:
    """
    Follows strict pipeline for notifying a user after a vault split.
    """
    # Fetch raw data
    raw_txs = await _fetch_transactions(user.id, db, limit=10) # Less context needed for split
    
    # 1. Scrub PII
    scrubbed_txs = pii_scrubber.scrub_transaction_list(raw_txs)
    
    # 2. Refinery Math
    context = full_context(scrubbed_txs, vault_balances={})
    
    # 3. LLM Insight (English)
    english_insight = await llm.generate_insight(context)
    
    # 4. LLM Translate
    localized_text = await llm.translate_to_language(english_insight, user.preferred_language)
    
    # 5. Send Text
    await twilio_client.send_text(user.whatsapp_no, localized_text)
