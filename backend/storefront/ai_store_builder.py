from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class StorePrompt(BaseModel):
    prompt: str


class ProductDescriptionPrompt(BaseModel):
    product_name: str
    short_notes: str | None = None
    target_customer: str | None = None
    category: str | None = None


def _infer_categories(prompt: str) -> list[str]:
    text = prompt.lower()
    if any(word in text for word in ["thrift", "cloth", "fashion", "wear", "shoe"]):
        return ["Shirts", "Jeans", "Shoes"]
    if any(word in text for word in ["food", "rice", "provision", "drink", "vegetable"]):
        return ["Foodstuff", "Drinks", "Household"]
    if any(word in text for word in ["phone", "gadget", "accessor"]):
        return ["Chargers", "Cases", "Earphones"]
    if any(word in text for word in ["skin", "beauty", "cosmetic"]):
        return ["Skincare", "Haircare", "Beauty"]
    return ["Popular Items", "New Arrivals", "Deals"]


@router.post("/generate-store")
async def generate_store(payload: StorePrompt):
    prompt = payload.prompt.strip()
    categories = _infer_categories(prompt)
    first = categories[0].replace("Foodstuff", "Provisions").replace("Popular Items", "Goods")
    store_name = "Campus Thrift Hub" if "thrift" in prompt.lower() else f"AAJE {first} Store"
    return {
        "store_name": store_name,
        "tagline": "Simple commerce for serious business",
        "description": prompt[:180] or "A clean AAJE storefront for customers to browse, order, and pay.",
        "categories": categories,
        "theme": {
            "style": "clean",
            "primary_color": "#111827",
            "layout": "simple_grid",
        },
        "starter_products": [
            {
                "name": f"Sample {categories[0]}",
                "category": categories[0],
                "description": "Add price, stock, and an image before publishing.",
                "suggested_price": None,
                "stock": 0,
            }
        ],
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
