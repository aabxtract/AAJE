import httpx
from app.config import settings

BASE = settings.mono_base_url
HEADERS = {
    "mono-sec-key": settings.mono_secret_key,
    "Content-Type": "application/json"
}

async def lookup_account(
    account_number: str,
    bank_code: str
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE}/v1/accounts/resolve",
            headers=HEADERS,
            json={
                "account_number": account_number,
                "bank_code": bank_code
            }
        )
        response.raise_for_status()
        return response.json()

async def generate_connect_url(user_id: str) -> str:
    return (
        f"https://connect.mono.co/?"
        f"key={settings.mono_public_key}"
        f"&reference={user_id}"
    )

async def get_transactions(
    account_id: str,
    start: str,
    end: str
) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE}/v1/accounts/{account_id}/transactions",
            headers=HEADERS,
            params={"start": start, "end": end, "paginate": False}
        )
        response.raise_for_status()
        return response.json().get("data", [])

async def get_account_details(account_id: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE}/v1/accounts/{account_id}",
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json().get("data", {})
