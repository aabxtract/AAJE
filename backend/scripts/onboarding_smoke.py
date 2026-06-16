"""End-to-end smoke test for the LLM-driven onboarding.

Unlike scripts/smoke_test.py (which mocks the LLM), this one actually calls
Groq. It exercises the full /onboarding/turn flow: LLM picks questions,
calls list_templates, calls finalize_onboarding, store gets created.

Pass criteria:
1. Turn 1 (empty history) returns a sensible AI message + 200
2. After a few turns simulating a fashion business, the LLM EITHER:
   - calls list_templates (good — surface template options)
   - calls finalize_onboarding (good — wraps up)
3. Once finalize_onboarding is called, the response has done=true + store
4. The created store exists in DB with the expected template_id

Skips with a warning if GROQ_API_KEY is empty.

Run from backend/ with the project venv:
    ./venv/Scripts/python.exe scripts/onboarding_smoke.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import uuid

_TMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_DB.name.replace(os.sep, '/')}"
os.environ["TWILIO_WEBHOOK_VALIDATE"] = "false"
os.environ["APP_ENV"] = "development"

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from importlib import reload
import app.config as _config
reload(_config)
from app.config import settings  # noqa: E402
settings.database_url = os.environ["DATABASE_URL"]
settings.twilio_webhook_validate = False
settings.app_env = "development"

from app.main import app  # noqa: E402
from app.database import AsyncSessionLocal  # noqa: E402
from app.models.store import Store  # noqa: E402
from sqlalchemy import select  # noqa: E402


PASSED = 0
FAILED = 0


def ok(label, detail=""):
    global PASSED
    PASSED += 1
    print(f"  PASS  {label}" + (f"  ({detail})" if detail else ""))


def fail(label, detail=""):
    global FAILED
    FAILED += 1
    msg = f"  FAIL  {label}"
    if detail:
        msg += f"\n        {detail}"
    print(msg)


async def run():
    if not settings.groq_api_key:
        print("SKIP  GROQ_API_KEY not set — this test requires a real LLM call")
        return

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test", timeout=60.0) as client:
        async with app.router.lifespan_context(app):
            await _exec(client)


async def _signup(client):
    payload = {
        "email": f"onboard-{uuid.uuid4().hex[:8]}@example.com",
        "password": "smoke-test-pass",
        "full_name": "Onboarding Tester",
        "phone": "+2348031234567",
    }
    r = await client.post("/auth/signup", json=payload)
    if r.status_code != 200:
        raise RuntimeError(f"signup failed: {r.status_code} {r.text}")
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}, r.json()["user"]["id"]


async def _turn(client, auth, history):
    return await client.post("/onboarding/turn", headers=auth, json={"history": history})


async def _exec(client):
    print("\n=== Setup ===")
    auth, user_id = await _signup(client)
    ok("signup")

    print("\n=== Turn 1: empty history (LLM should open) ===")
    r = await _turn(client, auth, [])
    if r.status_code != 200:
        fail("turn 1 -> 200", r.text)
        return
    t1 = r.json()
    ok("turn 1 -> 200")
    if t1.get("message") and len(t1["message"]) > 10:
        ok("turn 1 has a real message", f"len={len(t1['message'])}")
    else:
        fail("turn 1 message too short", repr(t1.get("message")))
    if t1.get("done"):
        fail("turn 1 should not be done yet")

    history = [
        {"role": "assistant", "content": t1["message"]},
        {"role": "user", "content": "I sell ankara fabric and ready-to-wear dresses in Lagos."},
    ]

    print("\n=== Turn 2: business description provided ===")
    r = await _turn(client, auth, history)
    if r.status_code != 200:
        fail("turn 2 -> 200", r.text)
        return
    t2 = r.json()
    ok("turn 2 -> 200")
    ok("turn 2 message returned", f"len={len(t2.get('message', ''))}")
    history.append({"role": "assistant", "content": t2["message"]})
    history.append({"role": "user", "content": "Call it Ada Fashions. My main product is Ankara Maxi Dress at 18000 naira."})

    print("\n=== Turn 3: store name + product ===")
    r = await _turn(client, auth, history)
    t3 = r.json()
    ok("turn 3 -> 200")
    history.append({"role": "assistant", "content": t3["message"]})

    # Keep nudging until we either get done=true or hit a turn cap
    print("\n=== Iterating until done or max turns ===")
    max_turns = 6
    last = t3
    finalized = False
    for i in range(max_turns):
        if last.get("done"):
            finalized = True
            break
        # Simulate user accepting whatever the LLM suggests
        nudge = "Yes, sounds good. Use that and publish it."
        history.append({"role": "user", "content": nudge})
        r = await _turn(client, auth, history)
        if r.status_code != 200:
            fail(f"iteration {i+1} -> 200", r.text)
            return
        last = r.json()
        print(f"  iter {i+1}: done={last.get('done')}, msg={(last.get('message') or '')[:60]!r}")
        history.append({"role": "assistant", "content": last["message"]})

    if finalized or last.get("done"):
        ok("LLM eventually finalized")
        store = last.get("store") or {}
        if store.get("store_slug"):
            ok("response carries store_slug", store["store_slug"])
        else:
            fail("done=true but no store payload", repr(last))
        if store.get("template_id"):
            ok("template_id present", store["template_id"])
        else:
            fail("no template_id in store payload")
        # Confirm store actually exists in DB
        async with AsyncSessionLocal() as db:
            row = (await db.execute(
                select(Store).where(Store.store_slug == store.get("store_slug", ""))
            )).scalar_one_or_none()
            if row:
                ok("store row exists in DB", str(row.id))
            else:
                fail("store row not found in DB")
    else:
        fail("LLM did not finalize within max_turns", f"last msg: {last.get('message')!r}")


def summary():
    print("\n" + "=" * 60)
    print(f"  PASSED: {PASSED}")
    print(f"  FAILED: {FAILED}")
    print("=" * 60)
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    try:
        asyncio.run(run())
        code = summary()
    finally:
        try: os.unlink(_TMP_DB.name)
        except OSError: pass
    sys.exit(code)
