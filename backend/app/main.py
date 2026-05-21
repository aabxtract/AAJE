import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import add_missing_model_columns, normalize_known_schema_drift, engine, Base
import app.models  # noqa: F401 — registers all SQLAlchemy models

from app.routes.webhook_whatsapp import router as whatsapp_webhook_router
from app.routes.auth import router as auth_v2_router
from app.routes.store import router as store_v2_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def _validate_production_config() -> None:
    """Refuse to start in production without the secrets the app depends on.

    No-op in development so local devs can run with blank .env values.
    """
    if settings.app_env == "development":
        return

    problems: list[str] = []
    if not settings.jwt_secret and settings.secret_key == "dev-secret-key":
        problems.append("JWT_SECRET (or SECRET_KEY) must be set")
    if not settings.meta_app_secret:
        problems.append("META_APP_SECRET must be set (webhook signature validation)")
    if not settings.meta_webhook_verify_token:
        problems.append("META_WEBHOOK_VERIFY_TOKEN must be set (webhook verification)")
    if not settings.frontend_url:
        problems.append("FRONTEND_URL must be set (CORS)")

    if problems:
        raise RuntimeError(
            "Production config invalid:\n  - " + "\n  - ".join(problems)
        )

# ── Optional/legacy routers ──────────────────────────────────────────────────
# Wrapped in try/except during the domain-per-folder → layer-per-concern
# restructure. Remove each try/except once the module is confirmed clean.

_whatsapp_router = None
_whatsapp_ecosystem_router = None
_whatsapp_flow_endpoint_router = None
_public_store_router = None
_storefront_events_router = None
_storefront_api_router = None
_auth_router = None
_dashboard_router = None
_wallet_router = None
_events_router = None
_payments_router = None
_marketing_router = None
_institutional_router = None
_bizprint_router = None
_storefront_router = None
_store_alias_router = None
_intelligence_ecosystem_router = None
_plans_router = None
_browser_flow_router = None
_squad_router = None
_mono_router = None
_intelligence_router = None
_admin_router = None

try:
    from app.whatsapp.routes import router as _whatsapp_router
except Exception as exc:
    logger.debug("whatsapp.routes skipped: %s", exc)

try:
    from app.routes.whatsapp_ecosystem import router as _whatsapp_ecosystem_router
except Exception as exc:
    logger.debug("whatsapp_ecosystem skipped: %s", exc)

try:
    from app.routes.whatsapp_flow_endpoint import router as _whatsapp_flow_endpoint_router
except Exception as exc:
    logger.debug("whatsapp_flow_endpoint skipped: %s", exc)

try:
    from app.routes.public_store import router as _public_store_router
except Exception as exc:
    logger.debug("public_store skipped: %s", exc)

try:
    from storefront.events import router as _storefront_events_router
except Exception as exc:
    logger.debug("storefront.events skipped: %s", exc)

try:
    from storefront.routes import router as _storefront_api_router
except Exception as exc:
    logger.debug("storefront.routes skipped: %s", exc)

try:
    from app.auth.routes import router as _auth_router
except Exception as exc:
    logger.debug("auth.routes skipped: %s", exc)

try:
    from app.routes.dashboard import router as _dashboard_router
except Exception as exc:
    logger.debug("dashboard skipped: %s", exc)

try:
    from app.routes.wallet import router as _wallet_router
except Exception as exc:
    logger.debug("wallet skipped: %s", exc)

try:
    from app.events.routes import router as _events_router
except Exception as exc:
    logger.debug("events.routes skipped: %s", exc)

try:
    from app.payments.routes import router as _payments_router
except Exception as exc:
    logger.debug("payments.routes skipped: %s", exc)

try:
    from app.campaigns.routes import router as _marketing_router
except Exception as exc:
    logger.debug("campaigns.routes skipped: %s", exc)

try:
    from app.routes.institutional import router as _institutional_router
except Exception as exc:
    logger.debug("institutional skipped: %s", exc)

try:
    from app.bizprint.routes import router as _bizprint_router
except Exception as exc:
    logger.debug("bizprint.routes skipped: %s", exc)

try:
    from app.storefront.routes import router as _storefront_router
except Exception as exc:
    logger.debug("storefront.routes (app) skipped: %s", exc)

try:
    from app.routes.store_aliases import router as _store_alias_router
except Exception as exc:
    logger.debug("store_aliases skipped: %s", exc)

try:
    from app.routes.intelligence_ecosystem import router as _intelligence_ecosystem_router
except Exception as exc:
    logger.debug("intelligence_ecosystem skipped: %s", exc)

try:
    from app.routes.plans import router as _plans_router
except Exception as exc:
    logger.debug("plans skipped: %s", exc)

try:
    from app.routes.browser_flow import router as _browser_flow_router
except Exception as exc:
    logger.debug("browser_flow skipped: %s", exc)

try:
    from app.payments.webhook import router as _squad_router
except Exception as exc:
    logger.debug("payments.webhook skipped: %s", exc)

try:
    from app.routes.mono_webhook import router as _mono_router
except Exception as exc:
    logger.debug("mono_webhook skipped: %s", exc)

try:
    from app.routes.intelligence_api import router as _intelligence_router
except Exception as exc:
    logger.debug("intelligence_api skipped: %s", exc)

try:
    from app.routes.admin import router as _admin_router
except Exception as exc:
    logger.debug("admin skipped: %s", exc)


@asynccontextmanager
async def lifespan(application: FastAPI):
    logger.info("AAJE API starting up...")

    _validate_production_config()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(add_missing_model_columns)
        await conn.run_sync(normalize_known_schema_drift)
    logger.info("Database tables verified/created")

    _stop_scheduler = None
    try:
        from scheduler import start_scheduler, stop_scheduler
        start_scheduler()
        _stop_scheduler = stop_scheduler
    except Exception:
        logger.debug("Scheduler not available")

    yield

    if _stop_scheduler:
        _stop_scheduler()
    await engine.dispose()
    logger.info("AAJE API shut down")


app = FastAPI(
    title="AAJE",
    version="1.0.0",
    description="WhatsApp-native business OS for Nigerian traders",
    lifespan=lifespan,
)

allowed_origins = [o for o in {settings.frontend_url, settings.app_public_url} if o]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Core routes (always registered) ─────────────────────────────────────────
app.include_router(whatsapp_webhook_router)
app.include_router(auth_v2_router)
app.include_router(store_v2_router)

# ── Legacy/optional routes (registered only if import succeeded) ─────────────
_optional: list[tuple] = [
    (_auth_router, {}),
    (_whatsapp_router, {}),
    (_whatsapp_flow_endpoint_router, {}),
    (_dashboard_router, {}),
    (_wallet_router, {}),
    (_events_router, {}),
    (_payments_router, {}),
    (_marketing_router, {}),
    (_institutional_router, {}),
    (_bizprint_router, {}),
    (_storefront_router, {}),
    (_store_alias_router, {}),
    (_whatsapp_ecosystem_router, {}),
    (_intelligence_ecosystem_router, {}),
    (_plans_router, {}),
    (_browser_flow_router, {}),
    (_squad_router, {}),
    (_mono_router, {}),
    (_intelligence_router, {}),
    (_admin_router, {"prefix": "/admin"}),
    (_public_store_router, {}),
    (_storefront_api_router, {"prefix": "/api/storefront", "tags": ["storefront"]}),
    (_storefront_events_router, {"prefix": "/api/events", "tags": ["storefront_events"]}),
]

for _router, _kwargs in _optional:
    if _router is not None:
        app.include_router(_router, **_kwargs)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "aaje-backend"}
