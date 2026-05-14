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
from app.database import engine, Base
from app.routes.webhook import router as whatsapp_router
from app.routes.whatsapp_flow_endpoint import router as whatsapp_flow_endpoint_router
from app.routes.public_store import router as public_store_router
from storefront.events import router as storefront_events_router
from storefront.routes import router as storefront_api_router

# Optional routers: import lazily so the server can run without every optional
# third-party integration installed. Missing integrations will be skipped.
browser_flow_router = None
intelligence_router = None
mono_router = None
squad_router = None
admin_router = None

try:
    from app.routes.browser_flow import router as browser_flow_router
except Exception:
    browser_flow_router = None

try:
    from app.routes.intelligence_api import router as intelligence_router
except Exception:
    intelligence_router = None

try:
    from app.routes.mono_webhook import router as mono_router
except Exception:
    mono_router = None

try:
    from app.routes.squad_webhook import router as squad_router
except Exception:
    squad_router = None

try:
    from app.routes.admin import router as admin_router
except Exception:
    admin_router = None

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
    description="WhatsApp-native financial OS for Nigerian market traders",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(whatsapp_router)
app.include_router(whatsapp_flow_endpoint_router)
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
app.include_router(public_store_router)
app.include_router(storefront_api_router, prefix="/api/storefront", tags=["storefront"])
app.include_router(storefront_events_router, prefix="/api/events", tags=["storefront_events"])


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.app_env}
