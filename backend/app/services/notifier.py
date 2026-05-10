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

logger = logging.getLogger(__name__)

async def send_daily_debrief(user, db) -> None:
    """
    Follows strict pipeline for daily debrief notification.
    """
    from app.services.slicer import get_daily_raw_context, calculate_refinery_signals
    
    # Fetch raw data
    raw_context = await get_daily_raw_context(user, db)
    
    # 1. Scrub PII
    scrubbed_context = pii_scrubber.scrub(raw_context)
    
    # 2. Refinery Math
    signals = calculate_refinery_signals(scrubbed_context)
    
    # 3. LLM Insight (English)
    english_insight = await llm.generate_insight(signals)
    
    # 4. LLM Translate
    localized_text = await llm.translate_to_language(english_insight, user.preferred_language)
    
    # 5. Send Text
    await twilio_client.send_text(user.whatsapp_no, localized_text)

async def notify_split(user, db, transaction_id: str) -> None:
    """
    Follows strict pipeline for notifying a user after a vault split.
    """
    from app.services.slicer import get_split_raw_context, calculate_refinery_signals
    
    # Fetch raw data
    raw_context = await get_split_raw_context(user, db, transaction_id)
    
    # 1. Scrub PII
    scrubbed_context = pii_scrubber.scrub(raw_context)
    
    # 2. Refinery Math
    signals = calculate_refinery_signals(scrubbed_context)
    
    # 3. LLM Insight (English)
    english_insight = await llm.generate_insight(signals)
    
    # 4. LLM Translate
    localized_text = await llm.translate_to_language(english_insight, user.preferred_language)
    
    # 5. Send Text
    await twilio_client.send_text(user.whatsapp_no, localized_text)
