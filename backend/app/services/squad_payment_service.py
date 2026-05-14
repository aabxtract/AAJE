import uuid
import logging
from typing import Dict

logger = logging.getLogger(__name__)


async def create_payment_link(order_id: uuid.UUID, amount: float) -> Dict[str, str]:
    """Simulate creating a Squad payment link / checkout session.

    In production this would call Squad's API and return a payment URL and reference.
    For MVP this returns a deterministic reference and a fake URL.
    """
    ref = f"SQ-{str(uuid.uuid4())}"
    url = f"https://pay.squad.example/checkout/{ref}"
    logger.info("Created simulated Squad payment link %s for order %s amount=%s", ref, order_id, amount)
    return {"reference": ref, "url": url}


async def verify_webhook(payload: Dict) -> bool:
    # Placeholder for signature verification; accept always in dev
    return True
