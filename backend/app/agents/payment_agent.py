import uuid
from datetime import datetime, timezone

from sqlalchemy import insert, select

from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.models.user import User
from app.models.vault import Vault
from app.redis import save_session
from app.services.mono import BANK_CODES
from app.payments.squad import transfer
from app.whatsapp.service import send_text
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


def _bank_code(value: str) -> str | None:
    cleaned = (value or "").strip().lower()
    if cleaned.isdigit():
        return cleaned
    return BANK_CODES.get(cleaned)


async def handle_add_supplier(whatsapp_no: str, message: str, session: dict):
    pending = session.setdefault("pending_data", {})
    pending["payment_flow"] = "supplier_name"
    pending["payment"] = {}
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What is the supplier's name?")


async def _ask_source_and_amount(whatsapp_no: str, session: dict):
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        user, rows = await _load_user_streams(db, whatsapp_no)
    if not user:
        await send_text(whatsapp_no, "I could not find your AAJE account.")
        return
    if not rows:
        await send_text(whatsapp_no, "You do not have an account to pay from yet.")
        return

    session.setdefault("pending_data", {})["payment_flow"] = "amount_source"
    await save_session(whatsapp_no, session)
    lines = ["How much and from which account? Reply like: 1 5000"]
    for index, (stream, vault) in enumerate(rows, start=1):
        lines.append(f"{index}. {stream.stream_name}: {format_naira(vault.current_balance or 0)}")
    await send_text(whatsapp_no, "\n".join(lines))


async def handle_payment(whatsapp_no: str, message: str, session: dict):
    pending = session.setdefault("pending_data", {})
    flow = pending.get("payment_flow")

    if flow == "supplier_name":
        name = message.strip()
        if len(name) < 2:
            await send_text(whatsapp_no, "Please enter a supplier name.")
            return
        pending.setdefault("payment", {})["supplier_name"] = name
        pending["payment_flow"] = "bank"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, "What bank is this supplier using? Example: GTBank, Access, Opay, Kuda")
        return

    if flow == "bank":
        code = _bank_code(message)
        if not code:
            await send_text(whatsapp_no, "I do not recognize that bank. Try GTBank, Access, Zenith, Opay, Kuda, or enter the bank code.")
            return
        pending.setdefault("payment", {})["bank_code"] = code
        pending["payment_flow"] = "account_number"
        await save_session(whatsapp_no, session)
        await send_text(whatsapp_no, "Enter the supplier's 10-digit account number.")
        return

    if flow == "account_number":
        account_number = message.strip().replace(" ", "")
        if not (account_number.isdigit() and len(account_number) == 10):
            await send_text(whatsapp_no, "That account number should be exactly 10 digits.")
            return
        pending.setdefault("payment", {})["account_number"] = account_number
        await _ask_source_and_amount(whatsapp_no, session)
        return

    if flow == "amount_source":
        from app.database import AsyncSessionLocal

        parts = message.replace(",", "").split()
        if len(parts) < 2 or not parts[0].isdigit():
            await send_text(whatsapp_no, "Reply with account number and amount. Example: 1 5000")
            return
        try:
            index = int(parts[0]) - 1
            amount = float(parts[1])
        except ValueError:
            await send_text(whatsapp_no, "Please enter the amount as a number. Example: 1 5000")
            return
        async with AsyncSessionLocal() as db:
            user, rows = await _load_user_streams(db, whatsapp_no)
        if not user or index < 0 or index >= len(rows):
            await send_text(whatsapp_no, "That account number is not on your list.")
            return
        stream, vault = rows[index]
        if amount <= 0:
            await send_text(whatsapp_no, "Payment amount must be more than zero.")
            return
        if float(vault.current_balance or 0) < amount:
            await send_text(whatsapp_no, f"{stream.stream_name} has only {format_naira(vault.current_balance or 0)}.")
            return
        payment = pending.setdefault("payment", {})
        payment["amount"] = amount
        payment["stream_id"] = str(stream.id)
        payment["stream_name"] = stream.stream_name
        pending.pop("payment_flow", None)
        session["awaiting_pin"] = True
        session["pin_action"] = "payment"
        await save_session(whatsapp_no, session)
        await send_text(
            whatsapp_no,
            f"Pay {format_naira(amount)} to {payment['supplier_name']} from {stream.stream_name}. Enter your PIN to confirm.",
        )
        return

    parts = [part.strip() for part in message.split(",")]
    if len(parts) >= 5:
        name, bank_value, account_number, amount_text, source_index = parts[:5]
        bank_code = _bank_code(bank_value)
        if not bank_code:
            await send_text(whatsapp_no, "I do not recognize that bank. Use a common bank name or bank code.")
            return
        try:
            amount = float(amount_text.replace(",", ""))
        except ValueError:
            await send_text(whatsapp_no, "Please enter the amount as a number.")
            return
        try:
            parsed_source_index = int(source_index)
        except ValueError:
            await send_text(whatsapp_no, "Source account must be a number from your account list.")
            return
        pending["payment"] = {
            "supplier_name": name,
            "bank_code": bank_code,
            "account_number": account_number,
            "amount": amount,
            "source_index": parsed_source_index,
        }
        session["awaiting_pin"] = True
        session["pin_action"] = "payment"
        await save_session(whatsapp_no, session)
        sent = await send_pin_confirm_flow(whatsapp_no, session, "this supplier payment")
        if sent:
            return
        await send_text(whatsapp_no, f"Pay {format_naira(float(amount.replace(',', '')))} to {name} ({account_number}). Enter your PIN to confirm.")
        return

    pending["payment_flow"] = "supplier_name"
    pending["payment"] = {}
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, "What is the supplier's name?")


async def execute_payment(whatsapp_no: str, session: dict, db):
    user, rows = await _load_user_streams(db, whatsapp_no)
    data = session.get("pending_data", {}).get("payment", {})
    if not user or not data:
        await send_text(whatsapp_no, "Payment details were not found.")
        return

    match = None
    if data.get("stream_id"):
        match = next(((s, v) for s, v in rows if str(s.id) == data.get("stream_id")), None)
    elif data.get("source_index"):
        index = int(data["source_index"]) - 1
        match = rows[index] if 0 <= index < len(rows) else None
    if not match:
        await send_text(whatsapp_no, "Payment source account was not found.")
        return

    amount = float(data["amount"])
    stream, vault = match
    if float(vault.current_balance or 0) < amount:
        await send_text(whatsapp_no, "Insufficient balance for this payment.")
        return

    reference = f"PAY-{uuid.uuid4().hex[:16].upper()}"
    await transfer(amount, data["bank_code"], data["account_number"], data["supplier_name"], "AAJE supplier payment", reference)
    vault.current_balance = float(vault.current_balance or 0) - amount
    vault.total_withdrawn = float(vault.total_withdrawn or 0) + amount
    await db.execute(insert(Transaction).values(
        user_id=user.id,
        stream_id=stream.id,
        amount=amount,
        type="debit",
        narration=f"Supplier payment to {data['supplier_name']}",
        category="payment",
        source="payment",
        squad_transaction_ref=reference,
        timestamp=datetime.now(timezone.utc),
        processed=True,
    ))
    await db.commit()
    session.get("pending_data", {}).pop("payment", None)
    session.get("pending_data", {}).pop("payment_flow", None)
    await save_session(whatsapp_no, session)
    await send_text(whatsapp_no, f"Payment successful. Ref: {reference}")
