from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class StorePrompt(BaseModel):
    prompt: str | None = None
    description: str | None = None


class ProductDescriptionPrompt(BaseModel):
    product_name: str
    short_notes: str | None = None
    target_customer: str | None = None
    category: str | None = None


def _template_for(prompt: str) -> dict:
    text = prompt.lower()
    if any(word in text for word in ["phone", "gadget", "accessor", "airpod", "charger", "laptop"]):
        return {
            "template": "gadgets",
            "store_name": "AAJE Gadget Studio",
            "tagline": "Trusted tech essentials, delivered fast",
            "categories": ["Audio", "Accessories", "Power"],
            "theme": "electric",
            "starter_products": [
                {"name": "AirPods Pro", "category": "Audio", "description": "Noise-cancelling wireless earbuds for work, calls, and music.", "price": 45000, "stock_quantity": 8, "low_stock_threshold": 2},
                {"name": "Fast USB-C Charger", "category": "Power", "description": "Compact 30W fast charger for phones and accessories.", "price": 12000, "stock_quantity": 12, "low_stock_threshold": 3},
                {"name": "MagSafe Phone Case", "category": "Accessories", "description": "Slim protective case with magnetic charging support.", "price": 9500, "stock_quantity": 10, "low_stock_threshold": 3},
            ],
        }
    if any(word in text for word in ["food", "rice", "provision", "drink", "vegetable", "snack", "meal"]):
        return {
            "template": "food",
            "store_name": "AAJE Kitchen Market",
            "tagline": "Fresh meals and provisions made easy",
            "categories": ["Meals", "Drinks", "Provisions"],
            "theme": "warm",
            "starter_products": [
                {"name": "Jollof Rice Bowl", "category": "Meals", "description": "Smoky party-style jollof with chicken and plantain.", "price": 5500, "stock_quantity": 15, "low_stock_threshold": 4},
                {"name": "Zobo Pack", "category": "Drinks", "description": "Chilled hibiscus drink, lightly spiced and bottled fresh.", "price": 1500, "stock_quantity": 25, "low_stock_threshold": 5},
                {"name": "Mini Provision Bundle", "category": "Provisions", "description": "Everyday pantry essentials bundled for convenience.", "price": 9000, "stock_quantity": 9, "low_stock_threshold": 2},
            ],
        }
    if any(word in text for word in ["creator", "course", "content", "design", "coach", "class"]):
        return {
            "template": "creator",
            "store_name": "AAJE Creator Studio",
            "tagline": "Digital products and services with instant checkout",
            "categories": ["Digital", "Services", "Coaching"],
            "theme": "creator",
            "starter_products": [
                {"name": "Brand Audit Session", "category": "Services", "description": "A focused review with clear next steps for your brand.", "price": 30000, "stock_quantity": 20, "low_stock_threshold": 3},
                {"name": "Content Calendar Template", "category": "Digital", "description": "A ready-to-use planning template for social content.", "price": 7500, "stock_quantity": 50, "low_stock_threshold": 5},
                {"name": "Creator Strategy Call", "category": "Coaching", "description": "One-on-one strategy session for launches and monetization.", "price": 45000, "stock_quantity": 10, "low_stock_threshold": 2},
            ],
        }
    return {
        "template": "fashion",
        "store_name": "AAJE Fashion House",
        "tagline": "Polished fashion pieces for everyday confidence",
        "categories": ["New Arrivals", "Accessories", "Essentials"],
        "theme": "minimal",
        "starter_products": [
            {"name": "Lagos Linen Shirt", "category": "New Arrivals", "description": "Breathable linen shirt with a clean premium fit.", "price": 18000, "stock_quantity": 10, "low_stock_threshold": 2},
            {"name": "Everyday Tote Bag", "category": "Accessories", "description": "Durable leather-feel tote for work, market, and weekends.", "price": 22000, "stock_quantity": 7, "low_stock_threshold": 2},
            {"name": "Classic Two-Piece Set", "category": "Essentials", "description": "Soft matching set designed for comfort and movement.", "price": 35000, "stock_quantity": 6, "low_stock_threshold": 2},
        ],
    }


@router.post("/generate-store")
async def generate_store(payload: StorePrompt):
    prompt = (payload.prompt or payload.description or "").strip()
    config = _template_for(prompt)
    if prompt:
        config["description"] = prompt[:180]
    else:
        config["description"] = "A polished AAJE storefront for customers to browse, order, and pay."
    return {
        **config,
        "products": config["starter_products"],
    }


@router.post("/generate-product-description")
async def generate_product_description(payload: ProductDescriptionPrompt):
    customer = payload.target_customer or "customers"
    notes = f" {payload.short_notes}" if payload.short_notes else ""
    category = payload.category or "General"
    return {
        "description": f"{payload.product_name} for {customer}.{notes} Clear, reliable, and ready for order through this AAJE store.",
        "sales_copy": f"Order {payload.product_name} today while stock is available.",
        "category": category,
    }
