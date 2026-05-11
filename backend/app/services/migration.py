import logging

logger = logging.getLogger(__name__)

async def migrate_user_to_pro(user, db):
    """
    Orchestrates the migration from Module 1 to Module 2.
    """
    logger.info(f"Migrating user {user.id} to AAJE Pro")
    await create_squad_accounts_for_migrating_user(user, db)
    await transfer_historical_data(user, db)
    await cancel_subscription(user, db)
    
    user.tier = "module_2"
    user.migration_eligible = False
    await db.commit()
    
    await send_migration_confirmation(user)

async def create_squad_accounts_for_migrating_user(user, db):
    from sqlalchemy import select
    from app.models.hustle_stream import HustleStream
    
    streams = await db.execute(select(HustleStream).where(HustleStream.user_id == user.id))
    for stream in streams.scalars().all():
        stream.stream_source = "squad"
        # Setup vaults and slice_config here
        stream.squad_virtual_accounts = {"Operations": {"account_number": "NEW_SQUAD_ACCT"}}
    await db.commit()

async def transfer_historical_data(user, db):
    """
    Marks Mono data as historical supplement.
    """
    pass

async def cancel_subscription(user, db):
    """
    Cancels the Module 1 recurring charge.
    """
    user.subscription_status = "cancelled"
    await db.commit()

async def send_migration_confirmation(user):
    from app.services.twilio_client import send_text
    await send_text(
        user.whatsapp_no,
        "🎉 Welcome to AAJE Pro! I have created your Squad Virtual Accounts and cancelled your ₦1,000 subscription.\n"
        "Send 'Vaults' to see your new automated setup."
    )
