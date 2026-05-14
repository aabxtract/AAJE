import html

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.database import AsyncSessionLocal
from app.services.flows import get_flow_session_by_token

router = APIRouter()


def _done_page() -> str:
    return """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AAJE Secure Action Complete</title>
    <style>
      :root { color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }
      body { margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 18px; background: Canvas; color: CanvasText; }
      main { width: min(100%, 420px); text-align: center; border: 1px solid color-mix(in srgb, CanvasText 16%, Canvas 84%); border-radius: 8px; padding: 28px 22px; }
      h1 { margin: 0 0 8px; font-size: 24px; letter-spacing: 0; }
      p { margin: 0; color: color-mix(in srgb, CanvasText 62%, Canvas 38%); line-height: 1.45; }
    </style>
  </head>
  <body><main><h1>Submitted</h1><p>You can return to WhatsApp. AAJE will confirm the action there.</p></main></body>
</html>"""


def _render_secure_flow_page(flow_session, token: str) -> str:
    flow_type = html.escape(flow_session.flow_type.replace("_", " ").title())
    safe_token = html.escape(token)
    payload = flow_session.payload_json or {}
    amount = html.escape(str(payload.get("amount", "")))
    amount_input = (
        f'<label><span>Amount</span><input name="amount" type="number" value="{amount}" required></label>'
        if flow_session.flow_type == "withdrawal"
        else ""
    )
    pin_input = (
        '<label><span>PIN</span><input name="pin" type="password" inputmode="numeric" minlength="4" maxlength="6" required></label>'
        if flow_session.flow_type in {"withdrawal", "pin_verification", "payout_account_change"}
        else ""
    )
    return f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AAJE {flow_type}</title>
    <style>
      :root {{ color-scheme: light dark; font-family: Inter, system-ui, sans-serif; }}
      body {{ margin: 0; min-height: 100vh; display: grid; place-items: center; padding: 18px; background: Canvas; color: CanvasText; }}
      main {{ width: min(100%, 430px); border: 1px solid color-mix(in srgb, CanvasText 16%, Canvas 84%); border-radius: 8px; overflow: hidden; }}
      header {{ padding: 16px 18px; border-bottom: 1px solid color-mix(in srgb, CanvasText 16%, Canvas 84%); font-weight: 800; }}
      form {{ padding: 18px; display: grid; gap: 14px; }}
      label {{ display: grid; gap: 7px; font-size: 13px; font-weight: 750; }}
      input {{ min-height: 46px; border-radius: 7px; border: 1px solid color-mix(in srgb, CanvasText 16%, Canvas 84%); padding: 0 12px; font: inherit; }}
      button {{ min-height: 48px; border: 0; border-radius: 7px; background: #128c7e; color: white; font: inherit; font-weight: 800; cursor: pointer; }}
      p {{ margin: 0; color: color-mix(in srgb, CanvasText 65%, Canvas 35%); line-height: 1.45; }}
    </style>
  </head>
  <body>
    <main>
      <header>AAJE {flow_type}</header>
      <form method="post" action="/flow/submit">
        <input type="hidden" name="token" value="{safe_token}">
        <p>Confirm this secure store operation. Sensitive actions are completed here, then confirmed in WhatsApp.</p>
        {amount_input}
        {pin_input}
        <button type="submit">Confirm</button>
      </form>
    </main>
  </body>
</html>"""


@router.get("/flow", response_class=HTMLResponse)
async def browser_flow(token: str):
    async with AsyncSessionLocal() as db:
        flow_session = await get_flow_session_by_token(db, token)
        if not flow_session:
            raise HTTPException(status_code=404, detail="Flow link expired")
        return _render_secure_flow_page(flow_session, token)


@router.get("/flow/state")
async def flow_state(token: str):
    async with AsyncSessionLocal() as db:
        flow_session = await get_flow_session_by_token(db, token)
        if not flow_session:
            raise HTTPException(status_code=404, detail="Flow link expired")
        return {
            "flow_type": flow_session.flow_type,
            "status": flow_session.status,
            "payload": flow_session.payload_json,
            "expires_at": flow_session.expires_at,
        }


@router.post("/flow/action")
async def flow_action(request: Request):
    body = await request.json()
    token = body.get("token")
    if not token:
        raise HTTPException(status_code=400, detail="Missing token")
    async with AsyncSessionLocal() as db:
        flow_session = await get_flow_session_by_token(db, token)
        if not flow_session:
            raise HTTPException(status_code=404, detail="Flow link expired")
        flow_session.payload_json = {
            **(flow_session.payload_json or {}),
            "last_action": body.get("action"),
            "action_payload": body.get("payload") or {},
        }
        await db.commit()
        return {"status": "saved", "flow_type": flow_session.flow_type}


@router.post("/flow/submit", response_class=HTMLResponse)
async def submit_browser_flow(request: Request, token: str = Form(...)):
    async with AsyncSessionLocal() as db:
        flow_session = await get_flow_session_by_token(db, token)
        if not flow_session:
            raise HTTPException(status_code=404, detail="Flow link expired")
        submitted = dict(await request.form())
        submitted.pop("token", None)
        flow_session.payload_json = {
            **(flow_session.payload_json or {}),
            "submitted": submitted,
        }
        flow_session.status = "submitted"
        await db.commit()
        return _done_page()
