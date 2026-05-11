def compute_combined_score(stream_scores: list[float]) -> float:
    """
    Aggregates scores across all hustle streams into one unified trader score.
    A trader with two consistent streams scores higher than the same trader with one stream.
    Formula: Max stream score + 10% bonus for each additional active stream (capped at 100).
    """
    if not stream_scores:
        return 0.0
    max_score = max(stream_scores)
    bonus = (len(stream_scores) - 1) * 10
    return min(round(max_score + bonus, 1), 100.0)

def compute_credit_grade(trader_score: float) -> str:
    """
    Maps trader score to a credit grade:
    A+ above 91, A from 81 to 91, B+ from 71 to 80, B from 61 to 70, C+ from 51 to 60, C from 41 to 50, D below 41.
    """
    if trader_score > 91: return "A+"
    elif trader_score >= 81: return "A"
    elif trader_score >= 71: return "B+"
    elif trader_score >= 61: return "B"
    elif trader_score >= 51: return "C+"
    elif trader_score >= 41: return "C"
    else: return "D"

def compute_loan_ceiling(credit_grade: str, avg_monthly_inflow: float) -> float:
    """
    Maps credit grade and average monthly inflow to a recommended loan ceiling amount.
    """
    multipliers = {
        "A+": 2.0,
        "A": 1.5,
        "B+": 1.0,
        "B": 0.75,
        "C+": 0.5,
        "C": 0.25,
        "D": 0.0
    }
    multiplier = multipliers.get(credit_grade, 0.0)
    return round(avg_monthly_inflow * multiplier, 2)
