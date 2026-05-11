import logging
import httpx
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import io
import re

logger = logging.getLogger(__name__)

async def process_receipt(whatsapp_no: str, media_url: str):
    from app.services.twilio_client import send_text
    from app.config import settings
    
    try:
        auth = (settings.twilio_account_sid, settings.twilio_auth_token)
        async with httpx.AsyncClient() as client:
            resp = await client.get(media_url, auth=auth)
            resp.raise_for_status()
            image_bytes = resp.content

        image = Image.open(io.BytesIO(image_bytes))
        
        # Preprocessing
        image = image.convert('L')
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        image = image.filter(ImageFilter.SHARPEN)

        # OCR
        text = pytesseract.image_to_string(image)
        
        # Regex for Naira amounts
        amounts = re.findall(r'(?:₦|NGN|N)?\s*([\d,]+\.?\d{0,2})', text)
        
        if amounts:
            max_amount = max([float(a.replace(',', '')) for a in amounts if a])
            await send_text(whatsapp_no, f"I detected an amount of ₦{max_amount:,.2f} from this receipt. Which business does this belong to?")
            # Ideally update session state here
        else:
            await send_text(whatsapp_no, "I couldn't read the amount clearly. Please send a clearer photo or type the amount.")
            
    except Exception as e:
        logger.error(f"OCR processing failed: {e}")
        await send_text(whatsapp_no, "I couldn't process this receipt right now. Please try again.")
