from fastapi import FastAPI

from app.routes.admin import router as admin_router
from app.routes.intelligence_api import router as intelligence_router
from app.routes.mono_webhook import router as mono_router
from app.routes.squad_webhook import router as squad_router
from app.routes.webhook import router as whatsapp_router


app = FastAPI(title="AAJE", version="1.0.0")

app.include_router(whatsapp_router)
app.include_router(squad_router)
app.include_router(mono_router)
app.include_router(intelligence_router)
app.include_router(admin_router, prefix="/admin")


@app.get("/health")
async def health():
    return {"status": "ok", "environment": "sandbox"}
