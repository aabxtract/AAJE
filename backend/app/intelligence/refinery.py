from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.models.income_stream import IncomeStream
from app.models.score import Score
from app.models.transaction import Transaction
from app.models.user import User


GRADE_CEILINGS = {
    "A+": Decimal("500000"),
    "A": Decimal("350000"),
    "B+": Decimal("200000"),
    "B": Decimal("150000"),
    "C+": Decimal("75000"),
    "C": Decimal("30000"),
    "D": Decimal("0"),
}


def _grade(score: float) -> str:
    if score >= 91:
        return "A+"
    if score >= 81:
        return "A"
    if score >= 71:
        return "B+"
    if score >= 61:
        return "B"
    if score >= 51:
        return "C+"
    if score >= 41:
        return "C"
    return "D"


async def compute_score(user_id: str, db) -> dict:
    user = await db.get(User, user_id)
    if not user:
        raise ValueError("User not found")

    tx_result = await db.execute(select(Transaction).where(Transaction.user_id == user_id))
    transactions = tx_result.scalars().all()

    now = datetime.now(timezone.utc)
    created_at = user.created_at or now
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    tenure_days = max((now - created_at).days, 1)

    if not transactions:
        scores = {
            "consistency_score": 0.0,
            "volume_score": 0.0,
            "savings_score": 0.0,
            "tenure_score": round(min(tenure_days / 90 * 25, 25), 1),
        }
    else:
        df = pd.DataFrame([
            {
                "amount": float(tx.amount),
                "type": tx.type,
                "timestamp": tx.timestamp,
                "stream_id": str(tx.stream_id) if tx.stream_id else None,
            }
            for tx in transactions
        ])
        credits = df[df["type"] == "credit"].copy()
        if credits.empty:
            scores = {"consistency_score": 0.0, "volume_score": 0.0, "savings_score": 0.0}
        else:
            credits["date"] = pd.to_datetime(credits["timestamp"]).dt.date
            active_days = credits["date"].nunique()
            total_credit = credits["amount"].sum()
            avg_daily_credit = total_credit / tenure_days

            stream_result = await db.execute(
                select(IncomeStream).where(IncomeStream.user_id == user_id)
            )
            saving_stream_ids = {
                str(stream.id)
                for stream in stream_result.scalars().all()
                if stream.is_savings or stream.is_emergency
            }
            savings_credit = credits[credits["stream_id"].isin(saving_stream_ids)]["amount"].sum()
            savings_ratio = savings_credit / total_credit if total_credit else 0

            scores = {
                "consistency_score": round(min(active_days / tenure_days * 25, 25), 1),
                "volume_score": round(min(avg_daily_credit / 50000 * 25, 25), 1),
                "savings_score": round(min(savings_ratio * 100, 25), 1),
            }

        scores["tenure_score"] = round(min(tenure_days / 90 * 25, 25), 1)

    trader_score = round(sum(scores.values()), 1)
    credit_grade = _grade(trader_score)
    result = {
        "trader_score": trader_score,
        "credit_grade": credit_grade,
        "recommended_loan_ceiling": GRADE_CEILINGS[credit_grade],
        **scores,
    }

    statement = insert(Score).values(user_id=user_id, **result)
    statement = statement.on_conflict_do_update(
        index_elements=[Score.user_id],
        set_={**result, "computed_at": now},
    )
    await db.execute(statement)
    await db.commit()
    return result
