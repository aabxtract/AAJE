import logging

logger = logging.getLogger(__name__)

async def charge_subscription(user, db):
    """
    Charges the 1,000 naira subscription fee for Module 1 users via Squad payment link/request.
    """
    logger.info(f"Charging subscription for user {user.id}")
    pass

async def handle_payment_failure(user, db):
    """
    Handles when a subscription payment fails. Enters grace period.
    """
    logger.info(f"Handling payment failure for user {user.id}")
    pass

async def check_subscription_status(user, db) -> str:
    """
    Returns the current status of the user's subscription.
    """
    return user.subscription_status

async def send_payment_reminder(user, db):
    """
    Sends a WhatsApp reminder to the user to pay their subscription.
    """
    from app.services.twilio_client import send_text
    await send_text(user.whatsapp_no, "Your AAJE Hustle-Manager subscription is due. Please pay to keep your intelligence active.")
