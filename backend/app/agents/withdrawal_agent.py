import uuid

from sqlalchemy import insert, select

from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault
from app.redis import save_session
from app.services.squad import transfer
from app.services.whatsapp_client import send_text
from app.services.whatsapp_flows import send_pin_confirm_flow
from app.utils.formatters import format_naira


async def _load_user_streams(db, whatsapp_no: str):
    user_result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
    user = user_result.scalar_one_or_none()
    if not user:
        return None, []
    stream_result = await db.execute(
        select(IncomeStream, Vault)
        .join(Vault, Vault.stream_id == IncomeStream.id)
        .where(IncomeStream.user_id == user.id)
    )
    return user, stream_result.all()


async def handle_withdrawal(whatsapp_no: str, message: str, session: dict):
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user, rows = await _load_user_streams(db, whatsapp_no)
    if not user:
        await send_text(whatsapp_no, "I could not find your AAJE account.")
        return

    parts = message.replace(",", "").split()
    if len(parts) >= 2 and parts[0].isdigit():
        index = int(parts[0]) - 1
        amount = float(parts[1])
        if index < 0 or index >= len(rows):
            await send_text(whatsapp_no, "That account number is not on your list.")
            return
        stream, vault = rows[index]
        session.setdefault("pending_data", {})["withdrawal"] = {
            "stream_id": str(stream.id),
            "stream_name": stream.stream_name,
            "amount": amount,
        }
        session["awaiting_pin"] = True
        session["pin_action"] = "withdrawal"
        await save_session(whatsapp_no, session)
        sent = await send_pin_confirm_flow(whatsapp_no, session, "this withdrawal")
        if sent:
            return
        await send_text(
            whatsapp_no,
            f"Withdraw {format_naira(amount)} from {stream.stream_name} to your {user.verified_bank_name} account ending {user.verified_bank_account[-4:]}. Enter your PIN to confirm.",
        )
        return

    lines = ["Which account and how much? Reply like: 1 5000"]
    for index, (stream, vault) in enumerate(rows, start=1):
        lines.append(f"{index}. {stream.stream_name}: {format_naira(vault.current_balance or 0)}")
    await send_text(whatsapp_no, "\n".join(lines))


async def execute_withdrawal(whatsapp_no: str, session: dict, db):
    user, rows = await _load_user_streams(db, whatsapp_no)
    data = session.get("pending_data", {}).get("withdrawal", {})
    stream_id = data.get("stream_id")
    amount = float(data.get("amount", 0))
    match = next(((s, v) for s, v in rows if str(s.id) == stream_id), None)
    if not user or not match:
        await send_text(whatsapp_no, "Withdrawal details were not found.")
        return
    stream, vault = match
    if float(vault.current_balance or 0) < amount:
        await send_text(whatsapp_no, "Insufficient balance for this withdrawal.")
        return

    reference = f"WD-{uuid.uuid4().hex[:16].upper()}"
    await transfer(amount, user.verified_bank_code, user.verified_bank_account, user.verified_bank_name or user.full_name, "AAJE withdrawal", reference)
    vault.current_balance = float(vault.current_balance or 0) - amount
    vault.total_withdrawn = float(vault.total_withdrawn or 0) + amount
    await db.execute(insert(Transaction).values(
        user_id=user.id,
        stream_id=stream.id,
        amount=amount,
        type="debit",
        narration="AAJE withdrawal",
        category="withdrawal",
        source="withdrawal",
        squad_transaction_ref=reference,
        timestamp=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        processed=True,
    ))
    await db.commit()
    session.get("pending_data", {}).pop("withdrawal", None)
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, f"Withdrawal complete. Ref: {reference}")
