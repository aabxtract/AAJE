import httpx
from app.config import settings

BASE = settings.squad_base_url
HEADERS = {
    "Authorization": f"Bearer {settings.squad_secret_key}",
    "Content-Type": "application/json"
}

async def register_customer(
    first_name: str,
    last_name: str,
    phone: str,
    account_number: str,
    bank_code: str
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE}/api/v1/merchant/customers",
            headers=HEADERS,
            json={
                "first_name": first_name,
                "last_name": last_name,
                "mobile_num": phone,
                "account_number": account_number,
                "bank_code": bank_code
            }
        )
        response.raise_for_status()
        return response.json().get("data", {})

async def create_virtual_account(
    customer_id: str,
    vault_name: str
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE}/api/v1/virtual-account",
            headers=HEADERS,
            json={
                "customer_identifier": customer_id,
                "preferred_bank": "wema-bank",
                "account_name": vault_name
            }
        )
        response.raise_for_status()
        return response.json().get("data", {})

async def transfer(
    amount: float,
    bank_code: str,
    account_number: str,
    account_name: str,
    narration: str,
    reference: str
) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE}/api/v1/payout/transfer",
            headers=HEADERS,
            json={
                "amount": int(amount * 100),  # kobo
                "bank_code": bank_code,
                "account_number": account_number,
                "account_name": account_name,
                "narration": narration,
                "transaction_reference": reference,
                "currency_id": "NGN"
            }
        )
        response.raise_for_status()
        return response.json().get("data", {})
