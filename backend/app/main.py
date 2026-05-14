"""
AAJE — WhatsApp-native financial operating system for Nigerian market traders.

This is the FastAPI entry point. It registers all routers, starts the
background scheduler, and creates database tables on first boot.
"""
import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import add_missing_sqlite_columns, engine, Base

from app.whatsapp.routes import router as whatsapp_router
from app.routes.whatsapp_ecosystem import router as whatsapp_ecosystem_router
from app.routes.whatsapp_flow_endpoint import router as whatsapp_flow_endpoint_router

# Optional/External routers
from app.routes.public_store import router as public_store_router
from storefront.events import router as storefront_events_router
from storefront.routes import router as storefront_api_router

# Core app routers
from app.auth.routes import router as auth_router
from app.routes.dashboard import router as dashboard_router
from app.routes.wallet import router as wallet_router
from app.events.routes import router as events_router
from app.payments.routes import router as payments_router
from app.campaigns.routes import router as marketing_router
from app.routes.institutional import router as institutional_router
from app.bizprint.routes import router as bizprint_router
from app.storefront.routes import router as storefront_router
from app.routes.store_aliases import router as store_alias_router
from app.routes.intelligence_ecosystem import router as intelligence_ecosystem_router

# Third-party or complex integrations with safety checks
browser_flow_router = None
intelligence_router = None
mono_router = None
squad_router = None
admin_router = None

try:
    from app.routes.browser_flow import router as browser_flow_router
except Exception:
    pass

try:
    from app.routes.intelligence_api import router as intelligence_router
except Exception:
    pass

try:
    from app.routes.mono_webhook import router as mono_router
except Exception:
    pass

try:
    from app.payments.webhook import router as squad_router
except Exception:
    pass

try:
    from app.routes.admin import router as admin_router
except Exception:
    pass

# Import all models so Base.metadata knows about them
import app.models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Startup / shutdown lifecycle."""
    # Startup
    logger.info("AAJE API starting up...")

    # Create tables if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(add_missing_sqlite_columns)
    logger.info("Database tables verified/created")

    # Start scheduler
    from scheduler import start_scheduler, stop_scheduler
    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    await engine.dispose()
    logger.info("AAJE API shut down")


app = FastAPI(
    title="AAJE",
    version="1.0.0",
    description="AI-native storefront, payments, WhatsApp control, and Squad Intelligence for African businesses",
    lifespan=lifespan,
)

allowed_origins = [origin for origin in {settings.frontend_url, settings.app_public_url} if origin]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Standard Routers
app.include_router(auth_router)
app.include_router(whatsapp_router)
app.include_router(whatsapp_flow_endpoint_router)
app.include_router(dashboard_router)
app.include_router(wallet_router)
app.include_router(events_router)
app.include_router(payments_router)
app.include_router(marketing_router)
app.include_router(institutional_router)
app.include_router(bizprint_router)
app.include_router(storefront_router)
app.include_router(store_alias_router)
app.include_router(whatsapp_ecosystem_router)
app.include_router(intelligence_ecosystem_router)

# Optional / External Routers
if browser_flow_router:
    app.include_router(browser_flow_router)
if squad_router:
    app.include_router(squad_router)
if mono_router:
    app.include_router(mono_router)
if intelligence_router:
    app.include_router(intelligence_router)
if admin_router:
    app.include_router(admin_router, prefix="/admin")

# Storefront v2 Routers
app.include_router(public_store_router)
app.include_router(storefront_api_router, prefix="/api/storefront", tags=["storefront"])
app.include_router(storefront_events_router, prefix="/api/events", tags=["storefront_events"])


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.app_env}

