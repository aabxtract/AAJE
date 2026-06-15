"""Storefront templates exposed for the React app + LLM onboarding tool.

GET /templates → full catalog (15 entries)
GET /templates/{template_id} → single template
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.intelligence.templates_catalog import get_template, list_templates

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("")
async def get_templates() -> dict:
    return {"templates": list_templates(), "count": len(list_templates())}


@router.get("/{template_id}")
async def get_one(template_id: str) -> dict:
    template = get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail=f"Unknown template: {template_id}")
    return template
