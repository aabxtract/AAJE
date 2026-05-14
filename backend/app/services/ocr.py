from app.whatsapp.service import send_text


async def process_receipt(whatsapp_no: str, _media_url: str):
    await send_text(whatsapp_no, "Receipt upload is not part of this MVP yet.")
