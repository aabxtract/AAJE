from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.models.user import User
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/ai", tags=["ai"])


class AssistRequest(BaseModel):
    task: str = Field(max_length=80)
    text: str = Field(default="", max_length=2000)
    context: dict = Field(default_factory=dict)


class AssistResponse(BaseModel):
    suggestion: str


@router.post("/assist", response_model=AssistResponse)
async def assist(
    body: AssistRequest,
    user: User = Depends(get_current_user),
) -> AssistResponse:
    task = body.task.strip().lower()
    text = body.text.strip()

    if task == "improve_description":
        return AssistResponse(suggestion=_improve_description(text))
    if task == "improve_title":
        return AssistResponse(suggestion=_title_case(text))
    if task == "generate_description":
        name = text or body.context.get("name") or "This product"
        category = body.context.get("category") or "your business"
        return AssistResponse(
            suggestion=f"{name} is a reliable {category} option for customers who want quality, clear value, and easy ordering."
        )
    if task == "suggest_category":
        return AssistResponse(suggestion=_suggest_category(text))
    if task == "operational_suggestions":
        return AssistResponse(suggestion=_operational_suggestion(body.context))

    return AssistResponse(
        suggestion="Focus on the next operational bottleneck: pending orders, missing product details, or low stock."
    )


def _improve_description(text: str) -> str:
    if not text:
        return "We sell quality products with fast responses, clear order tracking, and dependable customer service."
    return f"{text.rstrip('.')}. We keep orders organized, respond quickly, and make it easy for customers to buy with confidence."


def _title_case(text: str) -> str:
    cleaned = " ".join(text.split())
    return cleaned.title() if cleaned else "Clear Product Title"


def _suggest_category(text: str) -> str:
    lower = text.lower()
    if any(word in lower for word in ["shoe", "dress", "wear", "bag", "fashion"]):
        return "Fashion"
    if any(word in lower for word in ["course", "ebook", "template", "digital"]):
        return "Digital Products"
    if any(word in lower for word in ["hair", "makeup", "consult", "service"]):
        return "Services"
    if any(word in lower for word in ["food", "cake", "drink", "snack"]):
        return "Food"
    return "General"


def _operational_suggestion(context: dict) -> str:
    pending = int(context.get("pending_orders") or 0)
    low_stock = int(context.get("low_stock_products") or 0)
    products = int(context.get("product_count") or 0)
    if pending:
        return f"You have {pending} pending order{'s' if pending != 1 else ''}. Clear those first so customers are not left waiting."
    if low_stock:
        return f"{low_stock} product{'s are' if low_stock != 1 else ' is'} low on stock. Restock or hide unavailable items before new orders come in."
    if products < 3:
        return "Add your best-selling products first. A clean product list makes order tracking much easier."
    return "Your operations look steady. Review customer follow-ups and keep product stock counts current today."
