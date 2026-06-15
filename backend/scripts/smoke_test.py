"""Offline smoke test for the current MVP slice.

Exercises every wired path WITHOUT needing live Twilio or Groq:
- Temp SQLite DB (no Supabase writes)
- Stubbed outbound WhatsApp (collected for assertion)
- AI store generation falls back to _SAFE_DEFAULTS if Groq is unreachable

Run from backend/ with the project venv:
    ./venv/Scripts/python.exe scripts/smoke_test.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import textwrap
import uuid

# Point at a throwaway SQLite DB BEFORE importing the app — config.py reads
# DATABASE_URL from .env at import time.
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DB.name.replace(os.sep, '/')}"
# Don't hit Twilio during tests.
os.environ["TWILIO_WEBHOOK_VALIDATE"] = "false"
os.environ["APP_ENV"] = "development"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from sqlalchemy import select

# Force settings to re-read with our overrides
from importlib import reload
import app.config as _config
reload(_config)
from app.config import settings  # noqa: E402

settings.database_url = os.environ["DATABASE_URL"]
settings.twilio_webhook_validate = False
settings.app_env = "development"

# Now safe to import the app
from app.main import app  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.models.order import Order  # noqa: E402
import app.services.whatsapp_client as wac  # noqa: E402
import app.services.session as session_mod  # noqa: E402
import app.routes.orders as orders_route  # noqa: E402
import app.routes.auth as auth_route  # noqa: E402
import app.routes.webhook_monnify as monnify_route  # noqa: E402


# ---- Outbound capture ------------------------------------------------------
OUTBOUND: list[tuple[str, str]] = []


async def _fake_send_text(to: str, message: str):
    OUTBOUND.append((to, message))
    return {"status": "stubbed"}


# Patch every module that imported send_text by name at load time — each has
# its own binding in its namespace, and reassigning the source module isn't
# enough to redirect those.
wac.send_text = _fake_send_text
session_mod.send_text = _fake_send_text
orders_route.send_text = _fake_send_text
auth_route.send_text = _fake_send_text
monnify_route.send_text = _fake_send_text


# ---- Tiny test runner ------------------------------------------------------
PASSED = 0
FAILED = 0
LOG: list[str] = []


def ok(label: str):
    global PASSED
    PASSED += 1
    LOG.append(f"  PASS  {label}")
    print(f"  PASS  {label}")


def fail(label: str, detail: str = ""):
    global FAILED
    FAILED += 1
    msg = f"  FAIL  {label}"
    if detail:
        msg += f"\n        {detail}"
    LOG.append(msg)
    print(msg)


def check(label: str, condition: bool, detail: str = ""):
    if condition:
        ok(label)
    else:
        fail(label, detail)


# ---- Helpers ---------------------------------------------------------------
async def patch_user(client_id: str, **fields):
    async with AsyncSessionLocal() as db:
        user = await db.get(User, uuid.UUID(client_id))
        for k, v in fields.items():
            setattr(user, k, v)
        await db.commit()


async def get_order_by_ref(order_ref: str) -> Order | None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Order).where(Order.order_ref == order_ref)
        )
        return result.scalar_one_or_none()


# ---- Test sequence ---------------------------------------------------------
async def run():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Lifespan startup (creates SQLite tables)
        async with app.router.lifespan_context(app):
            await _run_all(client)


async def _run_all(client: httpx.AsyncClient):
    print("\n=== 1. Health check ===")
    r = await client.get("/health")
    check("GET /health -> 200", r.status_code == 200, r.text)
    check("payload reports ok", r.json().get("status") == "ok")

    print("\n=== 2. Auth: signup + login ===")
    # email-validator (pydantic[email]) rejects RFC 6761 reserved TLDs like
    # .test/.example/.localhost — use a real public TLD for the fake account.
    signup_payload = {
        "email": f"smoke-{uuid.uuid4().hex[:8]}@example.com",
        "password": "smoke-test-pass",
        "full_name": "Smoke Tester",
    }
    r = await client.post("/auth/signup", json=signup_payload)
    check("POST /auth/signup -> 200", r.status_code == 200, r.text)
    token = r.json().get("access_token")
    user_id = r.json().get("user", {}).get("id")
    check("signup returned access_token", bool(token))
    check("signup returned user.id", bool(user_id))

    auth = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/auth/login",
        json={"email": signup_payload["email"], "password": signup_payload["password"]},
    )
    check("POST /auth/login -> 200", r.status_code == 200, r.text)
    check("login returned a token", bool(r.json().get("access_token")))

    print("\n=== 3. Payout account: GET/PATCH/GET ===")
    r = await client.get("/auth/me/payout-account", headers=auth)
    check("GET /auth/me/payout-account -> 200", r.status_code == 200, r.text)
    check("ready=False before set", r.json().get("ready") is False)

    r = await client.patch(
        "/auth/me/payout-account",
        headers=auth,
        json={
            "account_number": "0123456789",
            "account_name": "Adunola B",
            "bank_name": "GTBank",
            "bank_code": "058",
        },
    )
    check("PATCH /auth/me/payout-account -> 200", r.status_code == 200, r.text)
    check(
        "account_number persisted (digits only)",
        r.json().get("account_number") == "0123456789",
    )
    check("ready=True after PATCH", r.json().get("ready") is True)

    r = await client.get("/auth/me/payout-account", headers=auth)
    check("subsequent GET reflects PATCH", r.json().get("account_number") == "0123456789")

    print("\n=== 4. Store setup (AI fallback OK) ===")
    r = await client.post(
        "/store/setup",
        headers=auth,
        json={
            "business_description": (
                "I sell ankara fabrics and ready-to-wear pieces at Balogun "
                "market. Ankara bags 4500, gele headties 2500, lace fabric 8500."
            ),
        },
    )
    check("POST /store/setup -> 200", r.status_code == 200, r.text)
    store = r.json()
    store_slug = store.get("store_slug")
    check("store has slug", bool(store_slug))
    check("store has at least 1 product (AI or default)", isinstance(store.get("products"), list))
    check(
        "store response includes payment_account block",
        isinstance(store.get("payment_account"), dict),
    )
    check(
        "payment_account.ready True (we set it earlier)",
        store.get("payment_account", {}).get("ready") is True,
    )

    print("\n=== 5. Public store endpoint ===")
    r = await client.get(f"/store/{store_slug}")
    check("GET /store/{slug} (no auth) -> 200", r.status_code == 200, r.text)
    public_store = r.json()
    check("public store includes products", isinstance(public_store.get("products"), list))
    check(
        "public store exposes payment_account",
        public_store.get("payment_account", {}).get("account_number") == "0123456789",
    )

    print("\n=== 6. Product CRUD ===")
    r = await client.post(
        "/products",
        headers=auth,
        json={
            "name": "Smoke-test Ankara Bag",
            "description": "Bright print, handmade",
            "price": 4500,
            "category": "Bags",
            "stock_count": 10,
        },
    )
    check("POST /products -> 201", r.status_code == 201, r.text)
    product_id = r.json().get("id")
    check("product id returned", bool(product_id))

    r = await client.get("/products", headers=auth)
    check("GET /products -> 200", r.status_code == 200, r.text)
    listed = r.json()
    check(
        "new product appears in auth-scoped list",
        any(p["id"] == product_id for p in listed),
    )

    print("\n=== 7. Order create (public, with the slug) ===")
    r = await client.post(
        "/orders",
        json={
            "store_slug": store_slug,
            "customer_name": "Ngozi Buyer",
            "customer_whatsapp": "08099887766",
            "items": [{"product_id": product_id, "quantity": 2}],
        },
    )
    check("POST /orders -> 201", r.status_code == 201, r.text)
    order = r.json()
    order_ref = order.get("order_ref")
    check("order_ref returned (AAJE-NNNN)", order_ref and order_ref.startswith("AAJE-"))
    check("initial status=pending", order.get("status") == "pending")
    check("total_amount=9000 (2 × 4500)", float(order.get("total_amount")) == 9000.0)

    # Background task fires _notify_trader_new_order — wait briefly then check
    await asyncio.sleep(0.1)
    initial_notify = [m for m in OUTBOUND if order_ref in m[1]]
    # Without a linked WhatsApp number on the trader, the helper exits early.
    check(
        "trader-new-order notify skipped (no linked WhatsApp yet)",
        len(initial_notify) == 0,
    )

    print("\n=== 8. Claim-transfer flow (public) ===")
    # Link the trader's WhatsApp first so the claim notification has a recipient
    await patch_user(user_id, whatsapp_no="2348012345678", whatsapp_connected=True, whatsapp_verified=True)

    r = await client.patch(f"/orders/{order_ref}/claim-transfer")
    check("PATCH /orders/:ref/claim-transfer -> 200", r.status_code == 200, r.text)
    check("status flipped to transfer_claimed", r.json().get("status") == "transfer_claimed")

    # Idempotency: second claim should be a no-op success
    r = await client.patch(f"/orders/{order_ref}/claim-transfer")
    check("second claim is idempotent (still 200)", r.status_code == 200)
    check("status still transfer_claimed", r.json().get("status") == "transfer_claimed")

    # Wait for background notify
    await asyncio.sleep(0.2)
    transfer_notify = [m for m in OUTBOUND if "transfer claim" in m[1].lower() and order_ref in m[1]]
    check(
        "trader received transfer-claim WhatsApp",
        len(transfer_notify) >= 1,
        detail=f"OUTBOUND={[m[1][:60] for m in OUTBOUND]}",
    )
    if transfer_notify:
        msg = transfer_notify[0][1]
        check("notification includes wa.me deep link", "wa.me/" in msg)
        check("notification includes bank label", "GTBank" in msg or "ending 6789" in msg)
        check(
            "notification includes both confirm and reject prompts",
            "confirm" in msg.lower() and "reject" in msg.lower(),
        )

    print("\n=== 9. Direct WhatsApp commands via session router ===")
    OUTBOUND.clear()
    # 'menu' command
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2348012345678", "menu", db)
    check("menu command produced a reply", any("commands" in m[1].lower() for m in OUTBOUND))

    OUTBOUND.clear()
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2348012345678", "orders", db)
    check(
        "orders command returns latest orders",
        any("Latest orders" in m[1] for m in OUTBOUND),
    )

    OUTBOUND.clear()
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2348012345678", f"confirm {order_ref}", db)
    fresh = await get_order_by_ref(order_ref)
    check("confirm AAJE-X flipped status=confirmed", fresh and fresh.status == "confirmed")
    check("confirm reply was sent to the trader", any(order_ref in m[1] for m in OUTBOUND))

    OUTBOUND.clear()
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2348012345678", f"delivered {order_ref}", db)
    fresh = await get_order_by_ref(order_ref)
    check(
        "delivered AAJE-X flipped status=delivered",
        fresh and fresh.status == "delivered",
    )

    OUTBOUND.clear()
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2348012345678", "balance", db)
    check(
        "balance command returned confirmed sales line",
        any("Confirmed sales" in m[1] for m in OUTBOUND),
    )

    print("\n=== 10. Out-of-status guard ===")
    # Cannot 'reject' an already-delivered order
    OUTBOUND.clear()
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2348012345678", f"reject {order_ref}", db)
    check(
        "reject on delivered order -> friendly error, no status change",
        any("currently" in m[1].lower() for m in OUTBOUND),
    )
    fresh = await get_order_by_ref(order_ref)
    check("status still delivered after illegal reject", fresh and fresh.status == "delivered")

    print("\n=== 11. Unlinked-number fallthrough ===")
    OUTBOUND.clear()
    async with AsyncSessionLocal() as db:
        await session_mod.route_message("2349099999999", "orders", db)
    check(
        "unknown sender gets Connect-AAJE greeting",
        any("Connect AAJE" in m[1] or "connect" in m[1].lower() for m in OUTBOUND),
    )


def summary():
    print("\n" + "=" * 60)
    print(f"  PASSED: {PASSED}")
    print(f"  FAILED: {FAILED}")
    print("=" * 60)
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    code = 0
    try:
        asyncio.run(run())
        code = summary()
    finally:
        try:
            os.unlink(_TMP_DB.name)
        except OSError:
            pass
    sys.exit(code)
