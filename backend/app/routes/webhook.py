import hashlib
import hmac
from html import escape
import json
import logging
from urllib.parse import quote

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from app.config import settings
from app.redis import set_rate_limit

logger = logging.getLogger(__name__)
router = APIRouter()


FLOW_ENDPOINT_FIELDS = {"encrypted_flow_data", "encrypted_aes_key", "initial_vector"}


def _mask_sender(sender: str | None) -> str:
    if not sender:
        return "unknown"
    return f"{sender[:4]}...{sender[-4:]}" if len(sender) > 8 else "masked"


def _verify_meta_signature(payload: bytes, signature: str) -> bool:
    if not signature.startswith("sha256="):
        return False
    expected = hmac.new(
        settings.meta_app_secret.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)


def _whatsapp_done_url() -> str:
    bot_number = "".join(ch for ch in settings.whatsapp_bot_number if ch.isdigit())
    if not bot_number:
        return "https://wa.me/"
    return f"https://wa.me/{bot_number}?text={quote('done')}"


def _return_page(helper_text: str, button_text: str = "Return to WhatsApp") -> str:
    safe_url = escape(_whatsapp_done_url(), quote=True)
    safe_button_text = escape(button_text)
    safe_helper_text = escape(helper_text)
    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Return to AAJE</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }}
      body {{
        margin: 0;
        min-height: 100vh;
        display: grid;
        place-items: center;
        background: #f7f7f2;
        color: #14211b;
      }}
      main {{
        width: min(420px, calc(100vw - 32px));
        text-align: center;
      }}
      h1 {{
        margin: 0 0 10px;
        font-size: 28px;
        line-height: 1.15;
        letter-spacing: 0;
      }}
      p {{
        margin: 0 0 22px;
        color: #4c5b52;
        line-height: 1.45;
      }}
      a {{
        display: inline-flex;
        align-items: center;
        justify-content: center;
        min-height: 48px;
        padding: 0 22px;
        border-radius: 8px;
        background: #128c7e;
        color: #fff;
        text-decoration: none;
        font-weight: 700;
      }}
    </style>
    <script>
      window.setTimeout(function () {{
        window.location.href = "{safe_url}";
      }}, 900);
    </script>
  </head>
  <body>
    <main>
      <h1>Bank connection received</h1>
      <p>{safe_helper_text}</p>
      <a href="{safe_url}">{safe_button_text}</a>
    </main>
  </body>
</html>
"""


async def process_message_safe(sender: str, message: str):
    try:
        from app.services.session import route_message

        await route_message(sender, message)
    except Exception:
        logger.exception("Message processing failed for %s", sender)
        try:
            from app.services.whatsapp_client import send_text

            await send_text(sender, "Something went wrong. Please try again in a moment.")
        except Exception:
            logger.exception("Failed to send fallback error message to %s", sender)


async def process_flow_response_safe(sender: str, flow_response: dict):
    try:
        from app.services.session import route_flow_response

        await route_flow_response(sender, flow_response)
    except Exception:
        logger.exception("Flow response processing failed for %s", sender)
        try:
            from app.services.whatsapp_client import send_text

            await send_text(sender, "Something went wrong with that secure screen. Please try again.")
        except Exception:
            logger.exception("Failed to send fallback flow error message to %s", sender)


@router.get("/webhook/whatsapp", response_class=PlainTextResponse)
async def verify_whatsapp_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_challenge: str = Query(alias="hub.challenge"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
):
    if hub_mode == "subscribe" and hub_verify_token == settings.meta_webhook_verify_token:
        logger.info("Meta WhatsApp webhook verification succeeded")
        return hub_challenge
    logger.warning("Meta WhatsApp webhook verification failed: mode=%s", hub_mode)
    raise HTTPException(status_code=403, detail="Invalid verify token")


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request, background_tasks: BackgroundTasks):
    payload = await request.body()
    signature = request.headers.get("x-hub-signature-256", "")
    if not _verify_meta_signature(payload, signature):
        logger.warning(
            "Rejected WhatsApp webhook: invalid signature header present=%s payload_bytes=%s",
            bool(signature),
            len(payload),
        )
        raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    if FLOW_ENDPOINT_FIELDS.issubset(data):
        from app.routes.whatsapp_flow_endpoint import handle_encrypted_flow_request
        from app.services.whatsapp_flow_crypto import FlowCryptoError

        try:
            encrypted_response = handle_encrypted_flow_request(data)
            return PlainTextResponse(encrypted_response)
        except FlowCryptoError as exc:
            logger.warning("Rejected Flow request sent to WhatsApp webhook URL: %s", exc)
            raise HTTPException(status_code=421, detail="Could not decrypt Flow request") from exc
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON") from exc

    value = (
        data.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
    )
    messages = value.get("messages") or []
    if not messages:
        logger.info("Ignored WhatsApp webhook without messages. keys=%s", sorted(value.keys()))
        return {"status": "ignored"}

    message = messages[0]
    sender = message.get("from")
    message_type = message.get("type")
    if sender and message_type == "interactive":
        from app.services.whatsapp_flows import extract_flow_response

        flow_response = extract_flow_response(message)
        if flow_response:
            count = await set_rate_limit(sender)
            if count > 10:
                from app.services.whatsapp_client import send_text

                logger.warning("Rate limited WhatsApp sender %s", _mask_sender(sender))
                await send_text(sender, "Please slow down. Try again in a minute.")
                return {"status": "rate_limited"}

            logger.info("Received WhatsApp Flow response from %s; queued processing", _mask_sender(sender))
            background_tasks.add_task(process_flow_response_safe, sender, flow_response)
            return {"status": "received"}

    if not sender or message_type != "text":
        logger.info(
            "Ignored WhatsApp message: sender=%s type=%s",
            _mask_sender(sender),
            message_type,
        )
        return {"status": "ignored"}

    body = (message.get("text") or {}).get("body", "").strip()
    if not body:
        logger.info("Ignored empty WhatsApp text from %s", _mask_sender(sender))
        return {"status": "ignored"}

    count = await set_rate_limit(sender)
    if count > 10:
        from app.services.whatsapp_client import send_text

        logger.warning("Rate limited WhatsApp sender %s", _mask_sender(sender))
        await send_text(sender, "Please slow down. Try again in a minute.")
        return {"status": "rate_limited"}

    logger.info("Received WhatsApp text from %s; queued processing", _mask_sender(sender))
    background_tasks.add_task(process_message_safe, sender, body)
    return {"status": "received"}


@router.get("/mono/return", response_class=HTMLResponse)
async def mono_return():
    helper_text = "WhatsApp will open with done ready to send."
    if not settings.whatsapp_bot_number:
        helper_text = "Set WHATSAPP_BOT_NUMBER in your backend .env to return directly to your bot."
    return _return_page(helper_text)


@router.get("/mono/mock-connect", response_class=HTMLResponse)
async def mono_mock_connect(reference: str = ""):
    safe_reference = escape(reference or "test-user")
    safe_return_url = escape(_whatsapp_done_url(), quote=True)
    return f"""
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>AAJE Connect</title>
    <style>
      :root {{
        color-scheme: light;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        --blue: #0b57d0;
        --deep-blue: #1120dc;
        --ink: #050505;
        --muted: #777777;
        --line: #ececec;
      }}
      * {{ box-sizing: border-box; }}
      body {{
        margin: 0;
        min-height: 100vh;
        background: #f3f4f8;
        color: var(--ink);
      }}
      button, input {{
        font: inherit;
      }}
      .phone {{
        width: min(100vw, 468px);
        min-height: 100vh;
        margin: 0 auto;
        background: #fff;
        position: relative;
        overflow: hidden;
        box-shadow: 0 18px 60px rgba(13, 24, 55, .14);
      }}
      .topbar {{
        height: 70px;
        border-bottom: 1px solid var(--line);
        display: grid;
        grid-template-columns: 54px 1fr 54px;
        align-items: center;
        padding: 0 10px;
      }}
      .icon-button {{
        width: 42px;
        height: 42px;
        border: 0;
        background: transparent;
        display: grid;
        place-items: center;
        cursor: pointer;
        color: #333;
      }}
      .brand {{
        text-align: center;
        color: #6c6c6c;
        font-size: 20px;
        font-weight: 800;
        letter-spacing: 0;
      }}
      .brand-mark {{
        display: inline-flex;
        gap: 2px;
        margin-right: 2px;
        vertical-align: 1px;
      }}
      .brand-mark i {{
        width: 9px;
        height: 9px;
        display: block;
        background: currentColor;
        transform: skew(28deg);
      }}
      .screen {{
        display: none;
        min-height: calc(100vh - 70px);
        padding: 20px 32px 32px;
      }}
      .screen.active {{
        display: block;
      }}
      .intro {{
        padding-top: 20px;
      }}
      .avatar {{
        width: 62px;
        height: 62px;
        border-radius: 50%;
        margin: 0 auto 34px;
        display: grid;
        place-items: center;
        background: #dcad85;
        color: #fff;
        font-size: 24px;
        font-weight: 800;
        box-shadow: 0 4px 9px rgba(0, 0, 0, .12);
      }}
      h1 {{
        margin: 0;
        font-size: 31px;
        line-height: 1.42;
        text-align: center;
        font-weight: 400;
      }}
      h1 strong {{
        font-weight: 800;
      }}
      h1 .blue {{
        color: #065ec9;
        font-weight: 800;
      }}
      .trust-box {{
        margin: 44px 0 34px;
        border: 1px solid var(--line);
        border-radius: 6px;
        padding: 4px 20px;
      }}
      .trust-row {{
        display: grid;
        grid-template-columns: 30px 1fr;
        gap: 16px;
        align-items: start;
        padding: 17px 0;
        color: #838383;
        line-height: 1.45;
        font-size: 15px;
      }}
      .trust-row strong {{
        color: #4a4a4a;
      }}
      .trust-icon {{
        color: #757575;
        padding-top: 2px;
      }}
      .smallprint {{
        margin: 0 0 20px;
        color: #898989;
        font-size: 14px;
        line-height: 1.55;
      }}
      .smallprint a {{
        color: #075fc8;
        font-weight: 700;
        text-decoration: none;
      }}
      .primary {{
        width: 100%;
        min-height: 68px;
        border: 0;
        border-radius: 6px;
        color: #fff;
        background: #075ec8;
        font-size: 22px;
        font-weight: 800;
        display: inline-flex;
        gap: 12px;
        align-items: center;
        justify-content: center;
        cursor: pointer;
      }}
      .bank-screen {{
        background: var(--deep-blue);
        padding: 10px 32px 24px;
      }}
      .search {{
        height: 42px;
        border: 1px solid rgba(255, 255, 255, .25);
        border-radius: 6px;
        background: rgba(255, 255, 255, .1);
        display: grid;
        grid-template-columns: 38px 1fr;
        align-items: center;
        color: #fff;
        padding: 0 14px 0 6px;
        margin-bottom: 12px;
      }}
      .search input {{
        min-width: 0;
        border: 0;
        outline: 0;
        background: transparent;
        color: #fff;
        height: 100%;
        font-weight: 700;
      }}
      .search input::placeholder {{
        color: rgba(255, 255, 255, .9);
      }}
      .bank-grid {{
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 11px;
      }}
      .bank-card {{
        min-height: 62px;
        border: 0;
        border-radius: 5px;
        background: #fff;
        display: grid;
        place-items: center;
        cursor: pointer;
      }}
      .bank-logo {{
        max-width: 128px;
        min-height: 34px;
        display: grid;
        place-items: center;
        font-weight: 900;
        letter-spacing: 0;
      }}
      .gtbank {{ color: #d15a20; }}
      .zenith {{ color: #6f6f6f; }}
      .firstbank {{ color: #092b66; font-size: 13px; }}
      .fcmb {{ color: #5b2780; }}
      .kuda {{ color: #5c2f83; font-size: 23px; }}
      .access {{ color: #244e9b; font-size: 20px; }}
      .barter {{ color: #151515; font-size: 21px; }}
      .fidelity {{ color: #1f6c42; font-size: 14px; }}
      .uba {{ color: #d31d28; font-size: 24px; }}
      .stanbic {{ color: #15559d; font-size: 13px; }}
      .standard {{ color: #1584b8; font-size: 13px; }}
      .alat {{ color: #c70f2e; font-size: 20px; }}
      .empty {{
        display: none;
        min-height: 360px;
        place-items: center;
        text-align: center;
        color: #fff;
      }}
      .empty.show {{ display: grid; }}
      .empty h2 {{
        margin: 12px 0 8px;
        font-size: 21px;
      }}
      .empty p {{
        margin: 0;
        max-width: 300px;
        color: rgba(255, 255, 255, .72);
        line-height: 1.45;
      }}
      .drawer-backdrop {{
        position: absolute;
        inset: 70px 0 0;
        background: rgba(0, 0, 0, .68);
        backdrop-filter: blur(4px);
        display: none;
        align-items: end;
        z-index: 4;
      }}
      .drawer-backdrop.show {{
        display: flex;
      }}
      .drawer {{
        width: 100%;
        background: #fff;
        border-radius: 18px 18px 0 0;
        padding: 20px 22px 28px;
      }}
      .selected-bank {{
        margin: 0 auto 16px;
        width: 58px;
        height: 42px;
        border-radius: 3px;
        background: #f8f8f8;
        display: grid;
        place-items: center;
        color: #d15a20;
        font-size: 11px;
        font-weight: 900;
      }}
      .drawer h2 {{
        text-align: center;
        font-size: 17px;
        margin: 0 0 22px;
      }}
      .method {{
        width: 100%;
        border: 0;
        border-bottom: 1px solid #eee;
        background: #fff;
        display: grid;
        grid-template-columns: 46px 1fr 24px;
        gap: 14px;
        text-align: left;
        padding: 18px 0;
        align-items: center;
        cursor: pointer;
      }}
      .method:last-child {{
        border-bottom: 0;
      }}
      .method-icon {{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: grid;
        place-items: center;
        background: #d6652a;
        color: #fff;
      }}
      .method strong {{
        display: block;
        color: #182039;
        font-size: 15px;
        margin-bottom: 3px;
      }}
      .method span {{
        color: #7a7f8d;
        font-size: 11px;
        line-height: 1.35;
      }}
      .form-screen {{
        padding-top: 34px;
      }}
      .form-screen h2, .done h2 {{
        margin: 0 0 8px;
        text-align: center;
        font-size: 25px;
      }}
      .lead {{
        margin: 0 auto 28px;
        color: #777;
        text-align: center;
        line-height: 1.45;
        max-width: 340px;
      }}
      .field {{
        margin-bottom: 14px;
      }}
      .field label {{
        display: block;
        color: #555;
        font-size: 13px;
        font-weight: 800;
        margin-bottom: 7px;
      }}
      .field input {{
        width: 100%;
        height: 54px;
        border: 1px solid #e1e1e1;
        border-radius: 6px;
        padding: 0 14px;
        outline: 0;
      }}
      .field input:focus {{
        border-color: #075ec8;
      }}
      .secure-note {{
        margin: 12px 0 24px;
        color: #777;
        font-size: 13px;
        line-height: 1.45;
      }}
      .loader {{
        width: 52px;
        height: 52px;
        border-radius: 50%;
        border: 5px solid #e7effc;
        border-top-color: #075ec8;
        margin: 72px auto 20px;
        animation: spin 1s linear infinite;
      }}
      @keyframes spin {{
        to {{ transform: rotate(360deg); }}
      }}
      .done {{
        text-align: center;
        padding-top: 70px;
      }}
      .check {{
        width: 74px;
        height: 74px;
        border-radius: 50%;
        display: grid;
        place-items: center;
        color: #fff;
        background: #118a50;
        margin: 0 auto 22px;
      }}
      .return-link {{
        margin-top: 24px;
        text-decoration: none;
      }}
      @media (min-width: 700px) {{
        body {{
          padding: 24px 0;
        }}
        .phone {{
          min-height: 720px;
          border-radius: 20px;
        }}
        .screen {{
          min-height: 650px;
        }}
        .drawer-backdrop {{
          inset: 70px 0 0;
          border-radius: 0 0 20px 20px;
        }}
      }}
    </style>
  </head>
  <body>
    <main class="phone">
      <header class="topbar">
        <button class="icon-button" type="button" data-back aria-label="Go back">
          <svg width="23" height="23" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M15 18l-6-6 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </button>
        <div class="brand"><span class="brand-mark"><i></i><i></i><i></i></span>AAJE</div>
        <button class="icon-button" type="button" data-close aria-label="Close">
          <svg width="23" height="23" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
        </button>
      </header>

      <section class="screen intro active" data-screen="intro">
        <div class="avatar">A</div>
        <h1><span class="blue">Aaje</span> uses <strong>AAJE Connect</strong><br>to link your account</h1>

        <div class="trust-box">
          <div class="trust-row">
            <div class="trust-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="2"/><path d="M3 12h18M12 3c2.4 2.7 3.6 5.7 3.6 9S14.4 18.3 12 21M12 3C9.6 5.7 8.4 8.7 8.4 12S9.6 18.3 12 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div>
            <div><strong>Trust.</strong> AAJE securely connects to supported financial institutions for your business profile.</div>
          </div>
          <div class="trust-row">
            <div class="trust-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M2.5 12s3.5-5 9.5-5 9.5 5 9.5 5-3.5 5-9.5 5-9.5-5-9.5-5z" stroke="currentColor" stroke-width="2"/><path d="M4 4l16 16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div>
            <div><strong>Private.</strong> This sandbox never sends bank credentials to a real institution.</div>
          </div>
          <div class="trust-row">
            <div class="trust-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="5" y="10" width="14" height="10" rx="1.5" stroke="currentColor" stroke-width="2"/><path d="M8 10V7a4 4 0 018 0v3" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></div>
            <div><strong>Secure.</strong> Test data is only used to continue the AAJE onboarding flow.</div>
          </div>
        </div>

        <p class="smallprint">By clicking 'Link account' you agree to AAJE's <a href="#">End-user Policy</a>. Reference: {safe_reference}. <a href="#">See details</a></p>
        <button class="primary" type="button" data-next="banks"><span class="brand-mark"><i></i><i></i><i></i></span> Link account</button>
      </section>

      <section class="screen bank-screen" data-screen="banks">
        <label class="search" aria-label="Search bank">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true"><circle cx="11" cy="11" r="7" stroke="currentColor" stroke-width="2"/><path d="M16.5 16.5L21 21" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
          <input id="bank-search" type="search" placeholder="Search" autocomplete="off">
        </label>
        <div class="bank-grid" id="bank-grid">
          <button class="bank-card" type="button" data-bank="GTBank"><span class="bank-logo gtbank">GTBank</span></button>
          <button class="bank-card" type="button" data-bank="Zenith"><span class="bank-logo zenith">ZENITH</span></button>
          <button class="bank-card" type="button" data-bank="FirstBank"><span class="bank-logo firstbank">FirstBank</span></button>
          <button class="bank-card" type="button" data-bank="FCMB"><span class="bank-logo fcmb">FCMB</span></button>
          <button class="bank-card" type="button" data-bank="Kuda"><span class="bank-logo kuda">kuda.</span></button>
          <button class="bank-card" type="button" data-bank="Access"><span class="bank-logo access">access</span></button>
          <button class="bank-card" type="button" data-bank="Barter"><span class="bank-logo barter">barter</span></button>
          <button class="bank-card" type="button" data-bank="Fidelity"><span class="bank-logo fidelity">Fidelity</span></button>
          <button class="bank-card" type="button" data-bank="UBA"><span class="bank-logo uba">UBA</span></button>
          <button class="bank-card" type="button" data-bank="Stanbic IBTC"><span class="bank-logo stanbic">Stanbic IBTC Bank</span></button>
          <button class="bank-card" type="button" data-bank="Standard Chartered"><span class="bank-logo standard">Standard Chartered</span></button>
          <button class="bank-card" type="button" data-bank="ALAT"><span class="bank-logo alat">ALAT</span></button>
        </div>
        <div class="empty" id="empty-state">
          <div>
            <svg width="62" height="62" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="3" y="3" width="18" height="18" rx="3" fill="rgba(255,255,255,.14)"/><circle cx="11" cy="11" r="4" stroke="rgba(255,255,255,.8)" stroke-width="1.5"/><path d="M14.5 14.5L18 18" stroke="rgba(255,255,255,.8)" stroke-width="1.5" stroke-linecap="round"/></svg>
            <h2>No institutions found</h2>
            <p>No institution available at the moment, please try again later.</p>
          </div>
        </div>
      </section>

      <section class="screen form-screen" data-screen="credentials">
        <h2 id="login-title">Log in securely</h2>
        <p class="lead" id="login-copy">Enter sandbox credentials to simulate bank linking. Any values work here.</p>
        <form id="credential-form">
          <div class="field">
            <label for="user-id">User ID</label>
            <input id="user-id" name="user-id" autocomplete="username" placeholder="Internet banking ID" required>
          </div>
          <div class="field">
            <label for="password">Password</label>
            <input id="password" name="password" type="password" autocomplete="current-password" placeholder="Password" required>
          </div>
          <p class="secure-note">This is AAJE's mock connect page. It does not contact Mono or your bank, and it should only be used for demo onboarding.</p>
          <button class="primary" type="submit">Continue</button>
        </form>
      </section>

      <section class="screen form-screen" data-screen="otp">
        <h2>Confirm access</h2>
        <p class="lead">Enter any 6 digits to complete the sandbox connection.</p>
        <form id="otp-form">
          <div class="field">
            <label for="otp">One-time code</label>
            <input id="otp" name="otp" inputmode="numeric" pattern="[0-9]{{6}}" maxlength="6" placeholder="123456" required>
          </div>
          <button class="primary" type="submit">Authorize</button>
        </form>
      </section>

      <section class="screen done" data-screen="processing">
        <div class="loader" aria-hidden="true"></div>
        <h2>Connecting account</h2>
        <p class="lead">Please wait while AAJE finishes this sandbox link.</p>
      </section>

      <section class="screen done" data-screen="done">
        <div class="check">
          <svg width="38" height="38" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M20 6L9 17l-5-5" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"/></svg>
        </div>
        <h2>Account linked</h2>
        <p class="lead">Return to WhatsApp and send <strong>done</strong> to continue your AAJE setup.</p>
        <a class="primary return-link" href="{safe_return_url}">Return to WhatsApp</a>
      </section>

      <div class="drawer-backdrop" id="drawer">
        <div class="drawer" role="dialog" aria-modal="true" aria-labelledby="method-title">
          <div class="selected-bank" id="selected-bank">GTBank</div>
          <h2 id="method-title">Choose log in method</h2>
          <button class="method" type="button" data-method="Internet Banking">
            <span class="method-icon"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="4" y="5" width="16" height="11" rx="1.5" stroke="currentColor" stroke-width="2"/><path d="M8 20h8M12 16v4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></span>
            <span><strong>Link with Internet Banking</strong><span>Credentials you use with your bank internet banking</span></span>
            <span aria-hidden="true">-&gt;</span>
          </button>
          <button class="method" type="button" data-method="Mobile Banking">
            <span class="method-icon"><svg width="19" height="19" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="7" y="3" width="10" height="18" rx="2" stroke="currentColor" stroke-width="2"/><path d="M11 17h2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg></span>
            <span><strong>Link with Mobile Banking</strong><span>Credentials you use with your bank mobile banking</span></span>
            <span aria-hidden="true">-&gt;</span>
          </button>
        </div>
      </div>
    </main>
    <script>
      const screens = Array.from(document.querySelectorAll('[data-screen]'));
      const drawer = document.getElementById('drawer');
      const selectedBank = document.getElementById('selected-bank');
      const search = document.getElementById('bank-search');
      const bankCards = Array.from(document.querySelectorAll('.bank-card'));
      const emptyState = document.getElementById('empty-state');
      const historyStack = ['intro'];
      let currentBank = 'GTBank';

      function show(name, push = true) {{
        screens.forEach((screen) => screen.classList.toggle('active', screen.dataset.screen === name));
        drawer.classList.remove('show');
        if (push && historyStack[historyStack.length - 1] !== name) {{
          historyStack.push(name);
        }}
      }}

      document.querySelectorAll('[data-next]').forEach((button) => {{
        button.addEventListener('click', () => show(button.dataset.next));
      }});

      document.querySelector('[data-back]').addEventListener('click', () => {{
        if (drawer.classList.contains('show')) {{
          drawer.classList.remove('show');
          return;
        }}
        if (historyStack.length > 1) {{
          historyStack.pop();
          show(historyStack[historyStack.length - 1], false);
        }}
      }});

      document.querySelector('[data-close]').addEventListener('click', () => {{
        show('intro');
      }});

      bankCards.forEach((card) => {{
        card.addEventListener('click', () => {{
          currentBank = card.dataset.bank;
          selectedBank.textContent = currentBank;
          drawer.classList.add('show');
        }});
      }});

      search.addEventListener('input', () => {{
        const term = search.value.trim().toLowerCase();
        let visible = 0;
        bankCards.forEach((card) => {{
          const match = card.dataset.bank.toLowerCase().includes(term);
          card.style.display = match ? 'grid' : 'none';
          if (match) visible += 1;
        }});
        emptyState.classList.toggle('show', visible === 0);
        document.getElementById('bank-grid').style.display = visible === 0 ? 'none' : 'grid';
      }});

      document.querySelectorAll('[data-method]').forEach((button) => {{
        button.addEventListener('click', () => {{
          document.getElementById('login-title').textContent = currentBank + ' login';
          document.getElementById('login-copy').textContent = 'Use ' + button.dataset.method.toLowerCase() + ' credentials to simulate linking this account.';
          show('credentials');
        }});
      }});

      document.getElementById('credential-form').addEventListener('submit', (event) => {{
        event.preventDefault();
        show('otp');
      }});

      document.getElementById('otp-form').addEventListener('submit', (event) => {{
        event.preventDefault();
        show('processing');
        window.setTimeout(() => show('done'), 1200);
      }});
    </script>
  </body>
</html>
"""
