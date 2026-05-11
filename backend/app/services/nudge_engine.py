import logging

logger = logging.getLogger(__name__)

async def check_nudge_eligibility(user, db) -> bool:
    """
    Checks if a Module 1 user is eligible for migration nudge.
    Conditions: > 60 days active, >= 2 payments, > 100k 30-day volume.
    """
    if user.tier != "module_1":
        return False
    # Stub: assume False by default
    return False

def calculate_comparison(volume_30d: float, subscription_paid: float) -> dict:
    """
    Calculates how much the user would have made in Module 2 vs what they paid in Module 1.
    """
    # Assuming 5% interest on average vault balance which scales with volume
    projected_interest = volume_30d * 0.05
    return {
        "fees_paid": subscription_paid,
        "projected_interest": projected_interest,
        "net_difference": projected_interest + subscription_paid
    }

async def send_nudge(user, comparison: dict, db):
    """
    Sends the AI nudge to migrate to AAJE Pro.
    """
    from app.services.twilio_client import send_buttons
    msg = (
        f"You've paid ₦{comparison['fees_paid']:,.2f} in fees so far.\n"
        f"If you were on AAJE Pro, you would have earned ₦{comparison['projected_interest']:,.2f} in interest instead.\n\n"
        f"Upgrade to AAJE Pro now for free. I will manage your vaults automatically."
    )
    await send_buttons(user.whatsapp_no, msg, ["Upgrade to AAJE Pro", "Not Now"])

async def log_nudge_sent(user, comparison: dict, db):
    """
    Logs the nudge to the nudge_log table.
    """
    from app.models.nudge_log import NudgeLog
    log = NudgeLog(
        user_id=user.id,
        trigger_volume_30d=100000, # Stub value
        trigger_subscription_paid=comparison['fees_paid'],
        projected_interest=comparison['projected_interest']
    )
    db.add(log)
    await db.commit()
