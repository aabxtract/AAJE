import httpx

from app.config import settings

BANK_CODES = {
    "gtbank": "058", "gtb": "058", "guaranty trust": "058", "guaranty trust bank": "058",
    "access": "044", "access bank": "044",
    "zenith": "057", "zenith bank": "057",
    "first bank": "011", "firstbank": "011", "fbn": "011",
    "uba": "033", "united bank for africa": "033",
    "union": "032", "union bank": "032",
    "fidelity": "070", "fidelity bank": "070",
    "sterling": "232", "sterling bank": "232",
    "wema": "035", "wema bank": "035",
    "kuda": "50211", "kuda bank": "50211",
    "opay": "999992", "opera": "999992",
    "palmpay": "999991", "palm pay": "999991",
    "moniepoint": "50515", "monie point": "50515",
}


async def lookup_account(account_number: str, bank_code: str) -> dict:
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            f"{settings.mono_base_url}/v1/accounts/resolve",
            headers={
                "mono-sec-key": settings.mono_secret_key,
                "Content-Type": "application/json",
            },
            json={"account_number": account_number, "bank_code": bank_code},
        )
    response.raise_for_status()
    return response.json().get("data", response.json())
