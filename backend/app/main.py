from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.routes.webhook import router as webhook_router
from app.routes.mono_webhook import router as mono_router
from app.routes.admin import router as admin_router
from scheduler import start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title="AAJE - Digital Business Manager",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(webhook_router, prefix="/webhook")
app.include_router(mono_router, prefix="/webhook")
app.include_router(admin_router, prefix="/admin")


@app.get("/health")
async def health():
    return {"status": "AAJE is live", "env": "sandbox"}
