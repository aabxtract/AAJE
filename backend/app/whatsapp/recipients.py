from app.config import settings
from app.models.commerce import Store
from app.models.user import User


def normalize_whatsapp_number(value: str | None) -> str | None:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    if not digits:
        return None
    if digits.startswith("0") and len(digits) == 11:
        return f"234{digits[1:]}"
    return digits


def normalize_whatsapp_numbers(value: str | None) -> list[str]:
    """Return one or more normalized WhatsApp numbers from an env-style value."""
    if not value:
        return []
    numbers: list[str] = []
    for part in str(value).replace("\n", ",").replace(";", ",").replace("|", ",").split(","):
        normalized = normalize_whatsapp_number(part)
        if normalized and normalized not in numbers:
            numbers.append(normalized)
    return numbers


def seller_notification_recipients(user: User | None = None, store: Store | None = None) -> list[str]:
    """Return all WhatsApp numbers Meta can message for seller-side demo alerts."""
    candidates = [
        settings.whatsapp_demo_recipient,
        settings.whatsapp_test_recipients,
        settings.whatsapp_registered_number,
        settings.whatsapp_registered_numbers,
        settings.meta_test_recipient_whatsapp_no,
        settings.meta_test_recipient_whatsapp_nos,
        user.whatsapp_no if user else None,
        store.contact_whatsapp if store else None,
        store.whatsapp_number if store else None,
    ]
    recipients: list[str] = []
    for candidate in candidates:
        for normalized in normalize_whatsapp_numbers(candidate):
            if normalized not in recipients:
                recipients.append(normalized)
    return recipients


def seller_notification_recipient(user: User | None = None, store: Store | None = None) -> str | None:
    """Return the primary WhatsApp number Meta can message for seller-side demo alerts."""
    recipients = seller_notification_recipients(user=user, store=store)
    return recipients[0] if recipients else None
