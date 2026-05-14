import hashlib
import hmac
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.config import settings
from app.services.whatsapp_flow_crypto import (
    FlowCryptoError,
    decrypt_flow_request,
    encrypt_flow_response,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def _verify_meta_signature(payload: bytes, signature: str) -> bool:
    if not signature:
        return True
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.meta_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _initial_data(flow_token: str) -> dict:
    return {"status": "legacy_whatsapp_flows_disabled"}


def _flow_response(request_body: dict) -> dict:
    action = request_body.get("action")
    screen = request_body.get("screen") or "START"
    data = request_body.get("data") or {}
    flow_token = request_body.get("flow_token") or data.get("flow_token") or ""

    if action == "ping":
        return {"data": {"status": "active"}}

    if isinstance(data, dict) and (data.get("error") or data.get("error_key")):
        return {"data": {"acknowledged": True}}

    if action in {"INIT", "BACK"}:
        return {"screen": screen, "data": _initial_data(flow_token)}

    if action == "data_exchange":
        params = {"flow_token": flow_token}
        if isinstance(data, dict):
            params.update(data)
        return {
            "screen": "SUCCESS",
            "data": {
                "extension_message_response": {
                    "params": params,
                }
            },
        }

    return {"screen": screen, "data": {}}


@router.post("/webhook/whatsapp/flows", response_class=PlainTextResponse)
async def whatsapp_flow_endpoint(request: Request):
    try:
        raw_body = await request.body()
        signature = request.headers.get("x-hub-signature-256", "")
        if not _verify_meta_signature(raw_body, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

        encrypted_body = json.loads(raw_body)
        decrypted_body, aes_key, initial_vector = decrypt_flow_request(encrypted_body)
        response = _flow_response(decrypted_body)
        return encrypt_flow_response(response, aes_key, initial_vector)
    except FlowCryptoError as exc:
        logger.warning("Rejected WhatsApp Flow endpoint request: %s", exc)
        raise HTTPException(status_code=421, detail="Could not decrypt Flow request") from exc
    except json.JSONDecodeError as exc:
        logger.warning("Rejected WhatsApp Flow endpoint request: invalid JSON")
        raise HTTPException(status_code=400, detail="Invalid JSON") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("WhatsApp Flow endpoint failed")
        raise HTTPException(status_code=500, detail="Flow endpoint failed") from exc


def handle_encrypted_flow_request(encrypted_body: dict) -> str:
    decrypted_body, aes_key, initial_vector = decrypt_flow_request(encrypted_body)
    response = _flow_response(decrypted_body)
    return encrypt_flow_response(response, aes_key, initial_vector)
