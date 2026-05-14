"""
The new Agentic runtime replacing the keyword based parser.
Orchestrates reasoning flow, loads context, executes tool calls, handles proactive behavior.
"""
import logging
import inspect

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.config import settings
from app.models.user import User
from app.intelligence.agent import agent_reason
from app.intelligence.context_builder import build_context, determine_persona
from app.intelligence import tools as intelligence_tools
from app.services.whatsapp_client import send_translated

logger = logging.getLogger(__name__)

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
                    if "message" in sig.parameters:
                        t_kwargs["message"] = str(message_or_event)
                    valid_kwargs = {k: v for k, v in t_kwargs.items() if k in sig.parameters}
                    res = await tool(**valid_kwargs)
                    tool_results.append((t_name, res))
                    logger.info("Tool %s returned: %s", t_name, res)
                except Exception as e:
                    logger.exception("Tool %s failed: %s", t_name, e)
            await db.commit()

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
    if name == "get_recent_orders" and isinstance(result, list):
        if not result:
            return "No recent orders yet."
        lines = ["Recent orders:"]
        for order in result[:5]:
            lines.append(
                f"- {order['short_id']}: {order['customer_name'] or 'Customer'} - "
                f"NGN {order['total_amount']:,.2f} - {order['payment_status']} / {order['order_status']}"
            )
        return "\n".join(lines)
    if name == "get_pending_orders" and isinstance(result, list):
        if not result:
            return "No pending orders right now."
        lines = ["Pending orders:"]
        for order in result[:5]:
            lines.append(f"- {order['short_id']}: NGN {order['total_amount']:,.2f} from {order['customer_name'] or 'Customer'}")
        return "\n".join(lines)
    if name == "get_low_stock_products" and isinstance(result, list):
        if not result:
            return "No products are below their low-stock threshold."
        lines = ["Low-stock products:"]
        for product in result[:6]:
            if isinstance(product, dict):
                lines.append(f"- {product['name']}: {product['stock_quantity']} left")
            else:
                lines.append(f"- {product.name}: {product.stock_quantity or 0} left")
        return "\n".join(lines)
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
    if name == "update_inventory_from_chat" and isinstance(result, dict):
        if result.get("error"):
            return result["error"]
        return f"Inventory updated: {result['product_name']} now has {result['stock_quantity']} in stock."
    if name == "create_product_from_chat_message" and isinstance(result, dict):
        if result.get("error"):
            return result["error"]
        return f"Product added: {result['name']} at NGN {result['price']:,.2f}, stock {result['stock_quantity']}."
    if name == "mark_order_fulfilled_from_chat" and isinstance(result, dict):
        if result.get("error"):
            return result["error"]
        return f"Order {result['short_id']} marked fulfilled."
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
