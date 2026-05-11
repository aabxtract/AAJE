from app.redis import save_session
from app.services.twilio_client import send_text
from sqlalchemy import select
from app.models.hustle_stream import HustleStream
from app.models.withdrawal import Withdrawal

async def handle_withdrawal(whatsapp_no: str, message: str, session: dict):
    # For now, simplistic implementation to show vaults and ask for input
    from app.database import AsyncSessionLocal
    from app.models.user import User
    
    async with AsyncSessionLocal() as db:
        user = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
        user = user.scalar_one_or_none()
        if not user:
            return
            
        streams_res = await db.execute(select(HustleStream).where(HustleStream.user_id == user.id))
        streams = streams_res.scalars().all()
        
        msg = "Here are your vault balances:\n\n"
        for s in streams:
            msg += f"*{s.stream_name}*\n"
            for v, data in s.squad_virtual_accounts.items():
                msg += f"- {v}: ₦XX,XXX\n" # Mock balance for demo
            msg += "\n"
            
        msg += "To withdraw, reply with the stream name, vault name, and amount.\nExample: Provisions, Savings, 5000"
        
        session["stage"] = "WITHDRAWAL_SELECTION"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, msg)

async def execute_withdrawal(whatsapp_no: str, session: dict, db):
    from app.services.squad import transfer
    from app.models.user import User
    
    user = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
    user = user.scalar_one_or_none()
    
    data = session.get("pending_data", {})
    amount = data.get("amount", 0)
    vault = data.get("vault")
    stream_id = data.get("stream_id")
    
    if not user.verified_bank_account:
        await send_text(whatsapp_no, "No verified bank account found.")
        return
        
    ref = f"wd_{user.id}_{int(amount)}"
    await transfer(user.verified_bank_account, user.verified_bank_code, int(amount * 100), f"Withdrawal from {vault}", ref)
    
    wd = Withdrawal(
        user_id=user.id,
        stream_id=stream_id,
        from_vault=vault,
        amount=amount,
        destination_account=user.verified_bank_account,
        squad_transfer_ref=ref,
        status='completed'
    )
    db.add(wd)
    await db.commit()
    
    await send_text(whatsapp_no, f"✅ Withdrawal of ₦{amount:,.2f} to your {user.verified_bank_name} account ending in {user.verified_bank_account[-4:]} is complete.")
