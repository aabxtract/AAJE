"""
Kolo slicer — the automated savings discipline engine.

When a trader reports revenue, AAJE automatically splits it into
locked digital vaults before the trader can reconsider.

Default split (configurable per trader):
  - 60% → Operations (day-to-day working capital)
  - 20% → Savings (locked growth vault)
  - 20% → Emergency (locked buffer vault)

Each split triggers:
  1. Squad transfer to the corresponding virtual account
  2. A ₦5 behavioral tax transfer to AAJE revenue account
  3. A vault_movement record in Postgres
"""
import logging
import uuid
from dataclasses import dataclass

from app.services import squad

logger = logging.getLogger(__name__)

DEFAULT_SPLITS = {
    "operations": 0.60,
    "savings": 0.20,
    "emergency": 0.20,
}

FEE_KOBO = 500  # ₦5 in kobo


@dataclass
class VaultConfig:
    vault_name: str
    account_number: str
    bank_code: str
    account_name: str


async def execute_split(
    amount_naira: float,
    vaults: list[VaultConfig],
    trader_id: str,
    custom_splits: dict[str, float] | None = None,
) -> list[dict]:
    """
    Split amount_naira across vaults and collect ₦5 fee per split.
    Returns a list of transfer results for Postgres logging.
    """
    splits = custom_splits or DEFAULT_SPLITS
    results = []

    for vault in vaults:
        ratio = splits.get(vault.vault_name, 0)
        if ratio <= 0:
            continue

        split_kobo = int(amount_naira * ratio * 100)
        ref = f"kolo-{trader_id}-{vault.vault_name}-{uuid.uuid4().hex[:8]}"

        try:
            transfer_result = await squad.transfer(
                amount=split_kobo,
                bank_code=vault.bank_code,
                account_number=vault.account_number,
                account_name=vault.account_name,
                narration=f"AAJE Kolo → {vault.vault_name}",
                reference=ref,
            )
            results.append({"vault": vault.vault_name, "result": transfer_result, "ref": ref})

            # Collect ₦5 behavioral tax
            fee_ref = f"fee-{ref}"
            await squad.collect_fee(FEE_KOBO, fee_ref)
            logger.info("₦5 fee collected | ref=%s", fee_ref)

        except Exception as exc:
            logger.error("Split failed for vault %s: %s", vault.vault_name, exc)
            results.append({"vault": vault.vault_name, "error": str(exc), "ref": ref})

    return results
