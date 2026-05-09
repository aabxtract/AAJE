"""
Formatters — shared display helpers for WhatsApp messages.
"""


def fmt_currency(amount: float) -> str:
    """Format a float as Nigerian Naira. Example: 18000.0 → ₦18,000.00"""
    return f"₦{amount:,.2f}"


def fmt_percent(value: float) -> str:
    """Format as percentage. Example: 0.6 → 60%"""
    return f"{value * 100:.0f}%"


def fmt_score(score: float) -> str:
    """Format trader score with label."""
    if score >= 80:
        label = "Excellent 🌟"
    elif score >= 60:
        label = "Good 👍"
    elif score >= 40:
        label = "Building 📈"
    else:
        label = "Just Starting 🌱"
    return f"{score:.1f}/100 — {label}"
