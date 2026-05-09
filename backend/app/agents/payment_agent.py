async def handle_payment(whatsapp_no: str, message: str, session: dict):
    from app.services.twilio_client import send_text
    await send_text(whatsapp_no, "Payment features will be available soon.")

async def execute_payment(whatsapp_no: str, session: dict, db):
    pass
