from datetime import datetime
from app.models.economic_identity import EconomicIdentity
from app.services.scorer import compute_combined_score, compute_credit_grade, compute_loan_ceiling

def build_economic_identity(user, stream_contexts: list[dict]) -> dict:
    """
    Assembles the complete Economic Identity object.
    Returns a structured dictionary with verified identity summary, multi-stream profile, etc.
    """
    # stream_contexts contains the outputs from refinery.py per stream
    stream_scores = [ctx.get("trader_score", 0.0) for ctx in stream_contexts]
    combined_score = compute_combined_score(stream_scores)
    
    # Module 1 penalty (approximate data from Mono)
    if user.tier == "module_1":
        combined_score = max(combined_score - 5.0, 0.0) # 5 point penalty
        
    credit_grade = compute_credit_grade(combined_score)
    
    data_source = "mono" if user.tier == "module_1" else "squad"
    data_quality = "standard" if user.tier == "module_1" else "verified"
    
    # Calculate average monthly inflow across all streams
    total_revenue_30d = sum(ctx.get("revenue_30d", 0.0) for ctx in stream_contexts)
    recommended_loan_ceiling = compute_loan_ceiling(credit_grade, total_revenue_30d)
    
    return {
        "verified_name": user.verified_bank_name,
        "business_type": user.business_type,
        "active_stream_count": len(stream_contexts),
        "trader_score": combined_score,
        "credit_grade": credit_grade,
        "recommended_loan_ceiling": recommended_loan_ceiling,
        "total_revenue_30d": total_revenue_30d,
        "data_source": data_source,
        "data_quality": data_quality,
        "passport_data": {
            "trader_score": combined_score,
            "credit_grade": credit_grade,
            "recommended_loan_ceiling": recommended_loan_ceiling,
            "active_stream_count": len(stream_contexts),
            "revenue_30d": total_revenue_30d,
            "data_source": data_source,
            "data_quality": data_quality,
            "streams": [
                {
                    "stream_score": ctx.get("trader_score", 0.0),
                    "revenue_30d": ctx.get("revenue_30d", 0.0),
                    "vault_health": ctx.get("vault_health", {})
                } for ctx in stream_contexts
            ]
        }
    }

async def save_identity_snapshot(user, stream_contexts: list[dict], db):
    """
    Writes the weekly snapshot to the economic_identities table.
    """
    identity_data = build_economic_identity(user, stream_contexts)
    
    snapshot = EconomicIdentity(
        user_id=user.id,
        snapshot_date=datetime.utcnow().date(),
        trader_score=identity_data["trader_score"],
        active_stream_count=identity_data["active_stream_count"],
        combined_credit_grade=identity_data["credit_grade"],
        data_quality_score=identity_data["data_quality"],
        recommended_loan_ceiling=identity_data["recommended_loan_ceiling"],
        total_inflow_30d=identity_data["total_revenue_30d"],
        passport_data=identity_data["passport_data"]
    )
    db.add(snapshot)
    await db.commit()
