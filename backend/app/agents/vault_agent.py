async def handle_vault_setup(whatsapp_no: str, message: str, session: dict):
    from app.redis import save_session
    from app.services.twilio_client import send_text
    
    data = session.get("pending_data", {})
    hustles = data.get("hustle_names", [])
    
    # Simple default vaults based on business type
    btype = data.get("business_type", "other")
    
    if "current_vault_index" not in data:
        data["current_vault_index"] = 0
        
    idx = data["current_vault_index"]
    
    if message.lower().strip() == "yes" and idx > 0:
        pass # Acknowledged previous vault setup

    if idx < len(hustles):
        stream_name = hustles[idx]
        vaults = ["Stock", "Savings", "Emergency", "Liquid"] if btype == "market_trader" else ["Operations", "Profit", "Emergency", "Liquid"]
        
        # Here we would call Squad API for each vault to get a virtual account
        # Mocking for now:
        vault_accounts = {v: {"account_number": "1234567890", "bank_name": "Squad"} for v in vaults}
        data[f"vaults_{idx}"] = vault_accounts
        
        data["current_vault_index"] = idx + 1
        session["pending_data"] = data
        
        if data["current_vault_index"] < len(hustles):
            await save_session(whatsapp_no, session)
            await send_text(
                whatsapp_no,
                f"For {stream_name}, I've created these vaults: {', '.join(vaults)}.\nReply 'Yes' to continue."
            )
        else:
            session["stage"] = "CONFIGURING_SLICES"
            data["current_slice_index"] = 0
            await save_session(whatsapp_no, session)
            await send_text(
                whatsapp_no,
                f"All vaults created! Now let's set how to divide money for {hustles[0]}.\n"
                f"Reply with percentages for {', '.join(vaults)} (e.g. 50,20,10,20):"
            )
    else:
        # Should not hit this
        pass

async def handle_slice_config(whatsapp_no: str, message: str, session: dict):
    from app.redis import save_session
    from app.services.twilio_client import send_text
    
    data = session.get("pending_data", {})
    hustles = data.get("hustle_names", [])
    idx = data.get("current_slice_index", 0)
    
    btype = data.get("business_type", "other")
    vaults = ["Stock", "Savings", "Emergency", "Liquid"] if btype == "market_trader" else ["Operations", "Profit", "Emergency", "Liquid"]
    
    # Parse percentages
    parts = [p.strip() for p in message.split(",")]
    if len(parts) != len(vaults):
        await send_text(whatsapp_no, f"Please provide {len(vaults)} numbers separated by commas.")
        return
        
    try:
        percentages = [int(p) for p in parts]
        if sum(percentages) != 100:
            await send_text(whatsapp_no, "The percentages must add up to 100. Try again:")
            return
            
        slice_config = {vaults[i]: percentages[i] for i in range(len(vaults))}
        data[f"slices_{idx}"] = slice_config
        
        idx += 1
        data["current_slice_index"] = idx
        session["pending_data"] = data
        
        if idx < len(hustles):
            await save_session(whatsapp_no, session)
            await send_text(
                whatsapp_no,
                f"Now for {hustles[idx]}.\nReply with percentages for {', '.join(vaults)} (e.g. 50,20,10,20):"
            )
        else:
            session["stage"] = "SETTING_DEBRIEF_TIME"
            await save_session(whatsapp_no, session)
            await send_text(
                whatsapp_no,
                "All slices configured!\n\nWhat time should I send your daily report?\n1. 7pm\n2. 8pm\n3. 9pm"
            )
    except ValueError:
        await send_text(whatsapp_no, "Please enter valid numbers.")

async def handle_vault(whatsapp_no: str, message: str, session: dict):
    # Placeholder for vault related intents like vault_balance, move_vault
    pass

async def execute_vault_move(whatsapp_no: str, session: dict, db):
    # Placeholder for PIN gated vault move action
    pass
