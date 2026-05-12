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
from app.routes.admin import router as admin_router
from app.routes.intelligence_api import router as intelligence_router
from app.routes.mono_webhook import router as mono_router
from app.routes.squad_webhook import router as squad_router
from app.routes.webhook import router as whatsapp_router

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
app.include_router(squad_router)
app.include_router(mono_router)
app.include_router(intelligence_router)
app.include_router(admin_router, prefix="/admin")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": settings.app_env}
