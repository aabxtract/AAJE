"""
PII Scrubber - Removes Personal Identifiable Information before sending data to LLM.
"""

def scrub(raw_context: dict) -> dict:
    """
    Scrubs PII (names, exact account numbers, phone numbers) from raw context.
    Returns safe context for LLM processing.
    """
    # Placeholder implementation
    scrubbed = raw_context.copy()
    if "account_number" in scrubbed:
        scrubbed["account_number"] = "***" + str(scrubbed["account_number"])[-4:]
    return scrubbed
