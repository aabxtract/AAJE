async def handle_summary(whatsapp_no: str, message: str, session: dict):
    from app.services.whatsapp_client import send_text
    await send_text(whatsapp_no, "Summary and insights features will be available soon.")
