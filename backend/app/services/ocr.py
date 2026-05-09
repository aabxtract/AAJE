"""
OCR service — extracts transaction amounts from trader receipt photos.

Pipeline:
  1. Download image from Twilio media URL
  2. Preprocess with Pillow (grayscale, contrast, denoise, rotate)
  3. Run Tesseract OCR
  4. Extract Naira amounts with regex tuned for Nigerian receipt formats
"""
import io
import logging
import re

import httpx
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

# Naira amount patterns: ₦18,000 | N18000 | NGN 18,000 | 18,000.00
_NAIRA_PATTERN = re.compile(
    r"(?:₦|N|NGN)\s*([\d,]+(?:\.\d{1,2})?)"
    r"|(\b[\d]{1,3}(?:,\d{3})+(?:\.\d{1,2})?\b)",
    re.IGNORECASE,
)


def _preprocess(image: Image.Image) -> Image.Image:
    """Enhance image quality for Tesseract accuracy."""
    image = image.convert("L")  # grayscale
    image = ImageEnhance.Contrast(image).enhance(2.5)
    image = image.filter(ImageFilter.MedianFilter(size=3))  # denoise
    # Upscale if too small (Tesseract needs ~300 DPI equivalent)
    w, h = image.size
    if w < 1000:
        scale = 1000 / w
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    return image


async def extract_amounts_from_url(media_url: str, auth: tuple[str, str]) -> list[float]:
    """
    Download image from Twilio URL, OCR it, return list of detected Naira amounts.
    auth: (twilio_account_sid, twilio_auth_token) for authenticated media fetch.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(media_url, auth=auth, timeout=15.0)
        resp.raise_for_status()
        raw = resp.content

    image = Image.open(io.BytesIO(raw))
    image = _preprocess(image)

    text = pytesseract.image_to_string(image, config="--psm 6")
    logger.debug("OCR raw text: %s", text[:300])

    amounts = []
    for match in _NAIRA_PATTERN.finditer(text):
        raw_amount = match.group(1) or match.group(2)
        try:
            clean = float(raw_amount.replace(",", ""))
            if clean > 0:
                amounts.append(clean)
        except ValueError:
            pass

    logger.info("OCR detected amounts: %s", amounts)
    return amounts
