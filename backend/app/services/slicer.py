async def get_daily_raw_context(user, db) -> dict:
    return {"raw_data": "daily info here"}

async def get_split_raw_context(user, db, transaction_id) -> dict:
    return {"raw_data": f"split info for {transaction_id}"}

def calculate_refinery_signals(scrubbed_context: dict) -> dict:
    return {"signals": "Refinery computed insights"}
