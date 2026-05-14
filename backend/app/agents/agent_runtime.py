"""
The new Agentic runtime replacing the keyword based parser.
Orchestrates reasoning flow, loads context, executes tool calls, handles proactive behavior.
"""
import logging
import inspect
from datetime import datetime, timezone

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.config import settings
from app.models.user import User
from app.models.vault import Vault
from app.models.income_stream import IncomeStream
from app.models.transaction import Transaction
from app.intelligence.agent import agent_reason
from app.intelligence.context_builder import build_context, determine_persona
from app.intelligence import tools as intelligence_tools
from app.intelligence.refinery import compute_score
from app.services.whatsapp_client import send_text, send_translated
from app.utils.pii_scrubber import scrub

logger = logging.getLogger(__name__)

async def load_trader_context(user: User, db) -> dict:
    # 1. Balances & streams
    vault_result = await db.execute(
        select(IncomeStream, Vault)
        .join(Vault, Vault.stream_id == IncomeStream.id)
        .where(IncomeStream.user_id == user.id)
    )
    vault_rows = vault_result.all()
    balances = {}
    active_streams = []
    for stream, vault in vault_rows:
        active_streams.append(stream.stream_name)
        balances[stream.stream_name] = float(vault.current_balance or 0)
    
    # 2. Score
    score_data = await compute_score(str(user.id), db)
    
    # 3. Recent transactions & days since last payment & largest payment this month
    tx_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.timestamp.desc())
    )
    transactions = tx_result.scalars().all()
    
    now = datetime.now(timezone.utc)
    days_since_last_payment = None
    largest_payment = 0
    if transactions:
        last_tx = transactions[0]
        timestamp = last_tx.timestamp
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        days_since_last_payment = (now - timestamp).days
        
        # Largest payment this month
        this_month_txs = [tx for tx in transactions if tx.timestamp.month == now.month and tx.timestamp.year == now.year and tx.type == "credit"]
        if this_month_txs:
            largest_payment = max(float(tx.amount) for tx in this_month_txs)
            
    loan_eligible = score_data.get("credit_grade") in ["A+", "A", "B+", "B"]
    
    context = {
        "balances": balances,
        "score": score_data.get("trader_score", 0),
        "score_trend": "stable",
        "days_since_last_payment": days_since_last_payment,
        "largest_payment_this_month": largest_payment,
        "loan_eligible": loan_eligible,
        "active_streams": active_streams,
        "language": user.preferred_language or "en",
        "recent_transactions": [{"amount": float(tx.amount), "type": tx.type, "narration": tx.narration} for tx in transactions[:5]]
    }
    
    return scrub(context)

# ----------------- TOOLS -----------------
async def get_vault_balances(user_id: str, db):
    vault_result = await db.execute(
        select(IncomeStream, Vault)
        .join(Vault, Vault.stream_id == IncomeStream.id)
        .where(IncomeStream.user_id == user_id)
    )
    return {stream.stream_name: float(vault.current_balance or 0) for stream, vault in vault_result.all()}

async def get_recent_transactions(user_id: str, days: int, db):
    tx_result = await db.execute(
        select(Transaction)
        .where(Transaction.user_id == user_id)
        .order_by(Transaction.timestamp.desc())
    )
    txs = tx_result.scalars().all()[:10]
    return [{"amount": float(tx.amount), "type": tx.type, "narration": tx.narration, "date": str(tx.timestamp)} for tx in txs]

async def get_score(user_id: str, db):
    return await compute_score(user_id, db)

async def execute_split(transaction_id: str, db):
    tx = await db.get(Transaction, transaction_id)
    if not tx: return "Transaction not found"
    return "Split executed (mock)"

async def assign_stream(transaction_id: str, stream_name: str, db):
    tx = await db.get(Transaction, transaction_id)
    if not tx: return "Transaction not found"
    
    stream_result = await db.execute(select(IncomeStream).where(IncomeStream.user_id == tx.user_id, IncomeStream.stream_name == stream_name))
    stream = stream_result.scalar_one_or_none()
    if stream:
        tx.stream_id = stream.id
        await db.commit()
        return f"Assigned to {stream_name}"
    return "Stream not found"

async def generate_insight_tool(user_id: str, db):
    user = await db.get(User, user_id)
    context = await load_trader_context(user, db)
    from app.intelligence.llm import generate_insight
    return await generate_insight(context)

async def send_account_number(user_id: str, stream_name: str, db):
    stream_result = await db.execute(select(IncomeStream).where(IncomeStream.user_id == user_id, IncomeStream.stream_name == stream_name))
    stream = stream_result.scalar_one_or_none()
    if stream and stream.squad_account_number:
        return f"Account number for {stream_name}: {stream.squad_account_number}"
    return "Account number not found"

async def update_split_config(user_id: str, percentages: dict, db):
    return "Split config updated (mock)"

async def flag_anomaly(user_id: str, anomaly_type: str, db):
    return f"Anomaly {anomaly_type} flagged."

async def initiate_withdrawal(user_id: str, whatsapp_no: str, stream_name: str, amount: float, session: dict, db):
    from app.services.whatsapp_flows import send_pin_confirm_flow
    from app.redis import save_session

    stream_result = await db.execute(select(IncomeStream).where(IncomeStream.user_id == user_id, IncomeStream.stream_name == stream_name))
    stream = stream_result.scalar_one_or_none()
    if not stream:
        return "Failed: Income stream not found."
        
    session.setdefault("pending_data", {})["withdrawal"] = {
        "stream_id": str(stream.id),
        "stream_name": stream.stream_name,
        "amount": amount,
    }
    session["awaiting_pin"] = True
    session["pin_action"] = "withdrawal"
    await save_session(whatsapp_no, session)
    
    sent = await send_pin_confirm_flow(whatsapp_no, session, "this withdrawal")
    if not sent:
        return "Failed: Could not send secure PIN flow. Please check WhatsApp configuration."
    return "Successfully initiated secure PIN flow for withdrawal."

async def initiate_payment(user_id: str, whatsapp_no: str, supplier_name: str, bank_code: str, account_number: str, amount: float, session: dict, db):
    from app.services.whatsapp_flows import send_pin_confirm_flow
    from app.redis import save_session

    session.setdefault("pending_data", {})["payment"] = {
        "supplier_name": supplier_name,
        "bank_code": bank_code,
        "account_number": account_number,
        "amount": amount,
    }
    session["awaiting_pin"] = True
    session["pin_action"] = "payment"
    await save_session(whatsapp_no, session)
    
    sent = await send_pin_confirm_flow(whatsapp_no, session, "this supplier payment")
    if not sent:
        return "Failed: Could not send secure PIN flow. Please check WhatsApp configuration."
    return "Successfully initiated secure PIN flow for payment."

AVAILABLE_TOOLS_MAP = {
    "get_vault_balances": get_vault_balances,
    "get_recent_transactions": get_recent_transactions,
    "get_score": get_score,
    "execute_split": execute_split,
    "assign_stream": assign_stream,
    "generate_insight": generate_insight_tool,
    "send_account_number": send_account_number,
    "update_split_config": update_split_config,
    "flag_anomaly": flag_anomaly,
    "initiate_withdrawal": initiate_withdrawal,
    "initiate_payment": initiate_payment
}
# -----------------------------------------

async def handle_event(whatsapp_no: str, message_or_event: str, session: dict = None):
    """
    Main entrypoint for agent reasoning.
    Replaces static intent router.
    """
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.whatsapp_no == whatsapp_no))
        user = result.scalar_one_or_none()
        if not user:
            logger.warning(f"User {whatsapp_no} not found for agent routing.")
            return

        persona = await determine_persona(db, user)
        context = await build_context(db, user, persona)
        tools_list = intelligence_tools.AVAILABLE_TOOL_NAMES

        # 1. Agent Reasoning
        decision = await agent_reason(message_or_event, context, tools_list)
        logger.info("Agent decision for %s: %s", whatsapp_no, decision)

        # 2. Proactive Actions / Tools Execution through Squad Intelligence tools.
        tools_to_call = decision.get("tools_to_call", [])
        tool_results = []
        if tools_to_call:
            logger.info("Executing tools: %s", tools_to_call)
            for t in tools_to_call:
                t_name = t.get("name") if isinstance(t, dict) else str(t)
                t_kwargs = t.get("kwargs", {}) if isinstance(t, dict) else {}
                if not hasattr(intelligence_tools, t_name):
                    continue
                tool = getattr(intelligence_tools, t_name)
                try:
                    sig = inspect.signature(tool)
                    if "db" in sig.parameters:
                        t_kwargs["db"] = db
                    if "user_id" in sig.parameters:
                        t_kwargs["user_id"] = str(user.id)
                    if "store_id" in sig.parameters and context.get("store"):
                        t_kwargs["store_id"] = context["store"]["id"]
                    valid_kwargs = {k: v for k, v in t_kwargs.items() if k in sig.parameters}
                    res = await tool(**valid_kwargs)
                    tool_results.append((t_name, res))
                    logger.info("Tool %s returned: %s", t_name, res)
                except Exception as e:
                    logger.exception("Tool %s failed: %s", t_name, e)

        # 3. Response Generation
        response_text = decision.get("response", "")
        if tool_results:
            response_text = _merge_tool_result_response(response_text, tool_results)
        if response_text:
            await send_translated(whatsapp_no, response_text, user.preferred_language or "en")


def _merge_tool_result_response(response_text: str, tool_results: list[tuple[str, object]]) -> str:
    name, result = tool_results[-1]
    if name == "generate_store_insight" and isinstance(result, str):
        return result
    if name == "get_top_products" and isinstance(result, list):
        if not result:
            return "I do not have enough product sales data yet."
        lines = [f"{index + 1}. {item['name']}: NGN {item['sales']:,.2f}" for index, item in enumerate(result)]
        return "Top products:\n" + "\n".join(lines)
    if name == "get_bizprint":
        return f"Your latest BizPrint summary: {result or 'not enough verified data yet'}"
    if name == "initiate_withdrawal" and isinstance(result, dict):
        token = result.get("flow_token")
        base = settings.app_public_url.rstrip("/") if settings.app_public_url else ""
        link = f"{base}/flow?token={token}" if token else ""
        return f"Secure withdrawal flow created. Complete PIN confirmation here: {link}\n\nNo money leaves AAJE without your PIN."
    if name == "get_marketing_analytics_tool" and isinstance(result, dict):
        summary = result.get("summary", {})
        sources = result.get("sources", [])
        campaigns = result.get("campaigns", [])
        if not sources and not campaigns:
            return "You don't have any marketing campaigns set up yet. Create them from the dashboard to track your growth."
        
        lines = ["Growth summary"]
        lines.append(f"Total Visits: {summary.get('total_visits', 0)}")
        lines.append(f"Product Views: {summary.get('total_product_views', 0)}")
        lines.append(f"Add to Cart: {summary.get('total_add_to_cart', 0)}")
        lines.append(f"Total Orders: {summary.get('total_orders', 0)}")
        lines.append(f"Total Revenue: NGN {summary.get('total_revenue', 0):,.2f}")
        lines.append(f"Best Channel: {summary.get('best_channel', 'N/A')}")
        if sources:
            lines.append("\nPerformance by source:")
            for item in sources[:3]:
                lines.append(
                    f"- {item['source']}: {item['orders']} order(s), "
                    f"NGN {item['revenue']:,.2f}, {item['conversion_rate']}% conversion"
                )
            for insight in result.get("insights", [])[:2]:
                lines.append(f"\n{insight}")
            return "\n".join(lines)
        lines.append("\n*Performance by Source:*")
        for c in campaigns[:3]:
            lines.append(f"- {c['source']}: {c['orders']} orders ({c['conversion_rate']}% conv)")
            
        return "\n".join(lines)
    return response_text
