import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, add_missing_model_columns, engine, normalize_known_schema_drift
import app.models  # noqa: F401 - registers SQLAlchemy models
from app.routes.ai_assist import router as ai_router
from app.routes.auth import router as auth_router
from app.routes.businesses import router as business_router
from app.routes.customers import router as customers_router
from app.routes.inventory import router as inventory_router
from app.routes.notifications import router as notifications_router
from app.routes.orders import router as orders_router
from app.routes.products import router as products_router
from app.routes.store import router as store_router
from app.routes.webhook_whatsapp import router as whatsapp_webhook_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def _validate_production_config() -> None:
    if settings.app_env == "development":
        return

    problems: list[str] = []
    if not settings.jwt_secret and settings.secret_key == "dev-secret-key":
        problems.append("JWT_SECRET or SECRET_KEY must be set")
    if not settings.frontend_url:
        problems.append("FRONTEND_URL must be set")
    if settings.twilio_webhook_validate and not settings.twilio_auth_token:
        problems.append("TWILIO_AUTH_TOKEN must be set when webhook validation is enabled")

    if problems:
        raise RuntimeError("Production config invalid:\n  - " + "\n  - ".join(problems))


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("AAJE operations API starting up...")
    _validate_production_config()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(add_missing_model_columns)
        await conn.run_sync(normalize_known_schema_drift)
    logger.info("Database tables verified/created")
    yield
    await engine.dispose()
    logger.info("AAJE operations API shut down")


app = FastAPI(
    title="AAJE",
    version="2.0.0",
    description="Operations workspace for Nigerian businesses already selling online",
    lifespan=lifespan,
)


def _split_origins(value: str) -> list[str]:
    return [origin.strip() for origin in (value or "").split(",") if origin.strip()]


allowed_origins = list(
    {
        *_split_origins(settings.frontend_url),
        *_split_origins(settings.app_public_url),
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_origin_regex=r"https?://([a-z0-9-]+\.)?(aaje\.store|localtest\.me)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(business_router)
app.include_router(store_router)
app.include_router(products_router)
app.include_router(orders_router)
app.include_router(inventory_router)
app.include_router(customers_router)
app.include_router(notifications_router)
app.include_router(ai_router)
app.include_router(whatsapp_webhook_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aaje-operations-api"}
