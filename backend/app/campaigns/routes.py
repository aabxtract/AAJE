import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.marketing import CampaignConversion, CampaignEvent, CampaignLink, CampaignVisit
from app.models.commerce import Product, Store

router = APIRouter(prefix="/api/marketing", tags=["marketing"])


class CampaignCreateRequest(BaseModel):
    store_id: str
    campaign_name: str
    source: str
    custom_source: str | None = None
    ref_slug: str | None = None


class CampaignTrackRequest(BaseModel):
    store_id: str
    ref: str
    event_type: Literal["visit", "product_view", "add_to_cart"] = "visit"
    session_id: str | None = None
    product_id: str | None = None


class CampaignLinkResponse(BaseModel):
    id: str
    campaign_name: str
    source: str
    ref_slug: str
    url: str


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:80] or "campaign"


def _storefront_url(store: Store, ref_slug: str) -> str:
    base = (settings.frontend_url or settings.app_public_url or "https://aaje.store").rstrip("/")
    return f"{base}/{store.slug}?ref={ref_slug}"


async def _unique_ref_slug(db: AsyncSession, store_id, base_slug: str) -> str:
    ref_slug = base_slug
    suffix = 2
    while (await db.execute(
        select(CampaignLink).where(CampaignLink.store_id == store_id, CampaignLink.ref_slug == ref_slug)
    )).scalar_one_or_none():
        ref_slug = f"{base_slug}_{suffix}"
        suffix += 1
    return ref_slug


async def find_campaign_by_ref(db: AsyncSession, store_id, ref: str) -> CampaignLink | None:
    return (await db.execute(
        select(CampaignLink).where(
            CampaignLink.store_id == store_id,
            CampaignLink.ref_slug == _slug(ref),
        )
    )).scalar_one_or_none()


async def record_campaign_visit(db: AsyncSession, campaign: CampaignLink, session_id: str | None = None) -> bool:
    if session_id:
        existing = (await db.execute(
            select(CampaignVisit).where(
                CampaignVisit.campaign_id == campaign.id,
                CampaignVisit.session_id == session_id,
            )
        )).scalar_one_or_none()
        if existing:
            return False
    db.add(CampaignVisit(
        campaign_id=campaign.id,
        store_id=campaign.store_id,
        session_id=session_id,
    ))
    return True


async def record_campaign_event(
    db: AsyncSession,
    campaign: CampaignLink,
    event_type: Literal["product_view", "add_to_cart"],
    session_id: str | None = None,
    product_id: str | None = None,
) -> CampaignEvent:
    if product_id:
        product = await db.get(Product, product_id)
        if not product or product.store_id != campaign.store_id:
            raise HTTPException(status_code=400, detail="Product does not belong to this store")
    event = CampaignEvent(
        campaign_id=campaign.id,
        store_id=campaign.store_id,
        product_id=product_id,
        session_id=session_id,
        event_type=event_type,
    )
    db.add(event)
    return event


@router.post("/campaigns", response_model=CampaignLinkResponse)
async def create_campaign(payload: CampaignCreateRequest, db: AsyncSession = Depends(get_db)):
    store = await db.get(Store, payload.store_id)
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")

    # Only premium users may create campaign links
    from app.models.user import User
    owner = await db.get(User, store.user_id)
    if not owner:
        raise HTTPException(status_code=404, detail="Store owner not found")
    if getattr(owner, "plan", "free") != "premium":
        raise HTTPException(status_code=403, detail="Campaign links are available to premium users only")

    source = _slug(payload.custom_source or payload.source)
    campaign_name = payload.campaign_name.strip()
    if not campaign_name:
        raise HTTPException(status_code=400, detail="Campaign name is required")

    base_ref_slug = _slug(payload.ref_slug or source)
    if payload.ref_slug:
        existing = await find_campaign_by_ref(db, store.id, payload.ref_slug)
        if existing:
            raise HTTPException(status_code=400, detail="Ref slug already exists for this store")
        ref_slug = base_ref_slug
    else:
        ref_slug = await _unique_ref_slug(db, store.id, base_ref_slug)

    campaign = CampaignLink(
        store_id=store.id,
        campaign_name=campaign_name,
        source=source,
        ref_slug=ref_slug
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    return {
        "id": str(campaign.id),
        "campaign_name": campaign.campaign_name,
        "source": campaign.source,
        "ref_slug": campaign.ref_slug,
        "url": _storefront_url(store, campaign.ref_slug)
    }


@router.post("/track")
async def track_campaign_event(payload: CampaignTrackRequest, db: AsyncSession = Depends(get_db)):
    campaign = await find_campaign_by_ref(db, payload.store_id, payload.ref)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    if payload.event_type == "visit":
        created = await record_campaign_visit(db, campaign, payload.session_id)
        await db.commit()
        return {"status": "tracked" if created else "already_tracked", "event_type": payload.event_type}

    await record_campaign_event(db, campaign, payload.event_type, payload.session_id, payload.product_id)
    await db.commit()
    return {"status": "tracked", "event_type": payload.event_type}


@router.get("/analytics/{store_id}")
async def get_marketing_analytics(store_id: str, days: int | None = None, db: AsyncSession = Depends(get_db)):
    campaigns = (await db.execute(select(CampaignLink).where(CampaignLink.store_id == store_id))).scalars().all()
    since = None
    if days and days > 0:
        since = datetime.now(timezone.utc) - timedelta(days=days)

    stats = []
    for campaign in campaigns:
        visit_query = select(func.count(CampaignVisit.id)).where(CampaignVisit.campaign_id == campaign.id)
        view_query = select(func.count(CampaignEvent.id)).where(
            CampaignEvent.campaign_id == campaign.id,
            CampaignEvent.event_type == "product_view",
        )
        cart_query = select(func.count(CampaignEvent.id)).where(
            CampaignEvent.campaign_id == campaign.id,
            CampaignEvent.event_type == "add_to_cart",
        )
        conversion_query = select(
            func.count(CampaignConversion.id),
            func.sum(CampaignConversion.revenue)
        ).where(CampaignConversion.campaign_id == campaign.id)
        if since:
            visit_query = visit_query.where(CampaignVisit.visited_at >= since)
            view_query = view_query.where(CampaignEvent.occurred_at >= since)
            cart_query = cart_query.where(CampaignEvent.occurred_at >= since)
            conversion_query = conversion_query.where(CampaignConversion.converted_at >= since)

        visits_count = (await db.execute(visit_query)).scalar() or 0
        product_views = (await db.execute(view_query)).scalar() or 0
        add_to_cart = (await db.execute(cart_query)).scalar() or 0
        result = (await db.execute(conversion_query)).first()

        orders_count = result[0] or 0
        revenue = float(result[1] or 0)
        conversion_rate = (orders_count / visits_count * 100) if visits_count > 0 else 0

        stats.append({
            "id": str(campaign.id),
            "campaign_name": campaign.campaign_name,
            "source": campaign.source,
            "ref_slug": campaign.ref_slug,
            "visits": visits_count,
            "product_views": product_views,
            "add_to_cart": add_to_cart,
            "orders": orders_count,
            "revenue": revenue,
            "conversion_rate": round(conversion_rate, 2)
        })

    by_source = {}
    for item in stats:
        source_stats = by_source.setdefault(item["source"], {
            "source": item["source"],
            "visits": 0,
            "product_views": 0,
            "add_to_cart": 0,
            "orders": 0,
            "revenue": Decimal("0"),
            "conversion_rate": 0,
        })
        source_stats["visits"] += item["visits"]
        source_stats["product_views"] += item["product_views"]
        source_stats["add_to_cart"] += item["add_to_cart"]
        source_stats["orders"] += item["orders"]
        source_stats["revenue"] += Decimal(str(item["revenue"]))

    source_stats = []
    for item in by_source.values():
        item["revenue"] = float(item["revenue"])
        item["conversion_rate"] = round((item["orders"] / item["visits"] * 100), 2) if item["visits"] else 0
        source_stats.append(item)
    source_stats.sort(key=lambda item: (item["revenue"], item["orders"], item["visits"]), reverse=True)

    highest_traffic = max(source_stats, key=lambda item: item["visits"])["source"] if source_stats else "None"
    best_revenue = max(source_stats, key=lambda item: item["revenue"])["source"] if source_stats else "None"
    best_conversion = max(source_stats, key=lambda item: item["conversion_rate"])["source"] if source_stats else "None"
    insights = []
    if source_stats:
        insights.append(f"{highest_traffic} drove your highest traffic source.")
        insights.append(f"{best_revenue} generated the most revenue.")
        if best_conversion != "None":
            insights.append(f"{best_conversion} converted best in this period.")

    return {
        "store_id": store_id,
        "period_days": days,
        "campaigns": stats,
        "sources": source_stats,
        "summary": {
            "total_visits": sum(s["visits"] for s in stats),
            "total_product_views": sum(s["product_views"] for s in stats),
            "total_add_to_cart": sum(s["add_to_cart"] for s in stats),
            "total_orders": sum(s["orders"] for s in stats),
            "total_revenue": sum(s["revenue"] for s in stats),
            "highest_traffic_source": highest_traffic,
            "best_channel": best_revenue,
            "best_converting_source": best_conversion,
        },
        "insights": insights,
    }
