async def handle_withdrawal(whatsapp_no: str, message: str, session: dict):
    from app.services.twilio_client import send_text
    await send_text(whatsapp_no, "Withdrawal features will be available soon.")

async def execute_withdrawal(whatsapp_no: str, session: dict, db):
    pass
