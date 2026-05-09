async def process_receipt(whatsapp_no: str, media_url: str):
    from app.services.twilio_client import send_text
    await send_text(whatsapp_no, "Receipt processing features will be available soon.")
