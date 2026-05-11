import logging
from app.services.squad import transfer
from app.config import settings
from sqlalchemy.sql import insert
from app.models.vault_movement import VaultMovement

logger = logging.getLogger(__name__)

def _apply_rules(user, transaction: dict, slice_config: dict) -> dict:
    # Level 2 rule-based adjustments
    # Simplified for hackathon: return base config
    return slice_config

async def execute_split(user, transaction: dict, stream_id: str, db):
    """
    Auto-splits incoming credit into the stream's vaults.
    """
    from sqlalchemy import select
    from app.models.hustle_stream import HustleStream
    
    stream_result = await db.execute(select(HustleStream).where(HustleStream.id == stream_id))
    stream = stream_result.scalar_one_or_none()
    
    if not stream or not stream.slice_config:
        logger.warning(f"No slice config found for stream {stream_id}")
        return
        
    amount_kobo = int(transaction.get("amount", 0) * 100)
    if amount_kobo <= 0:
        return
        
    amount_to_split = amount_kobo
    
    if amount_to_split <= 0:
        return
        
    adjusted_config = _apply_rules(user, transaction, stream.slice_config)
    
    for vault_name, percentage in adjusted_config.items():
        if percentage <= 0:
            continue
            
        vault_amount = int((percentage / 100.0) * amount_to_split)
        if vault_amount <= 0:
            continue
            
        vault_account_number = stream.squad_virtual_accounts.get(vault_name, {}).get("account_number")
        bank_code = stream.squad_virtual_accounts.get(vault_name, {}).get("bank_code", "000000")
        
        if vault_account_number:
            ref = f"split_{transaction['id']}_{vault_name}"
            # Squad transfer requires bank code, using dummy or stored
            await transfer(vault_account_number, bank_code, vault_amount, f"Split to {vault_name}", ref)
            
            # Log movement
            movement = VaultMovement(
                user_id=user.id,
                stream_id=stream_id,
                source_transaction_id=transaction["id"],
                vault_name=vault_name,
                amount=vault_amount / 100.0,
                direction="in",
                squad_transfer_ref=ref,
                fee_charged=0
            )
            db.add(movement)
            
    await db.commit()
    
    # Notify trader
    from app.services.notifier import notify_split
    await notify_split(user, db, str(transaction["id"]))
