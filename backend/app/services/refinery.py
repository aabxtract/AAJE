"""
Analytics refinery — pure Python math, no external API calls.

Always runs BEFORE the LLM to produce structured, scrubbed context.
The LLM never sees raw transaction data.

Computes:
  - Revenue, expense, and profit summaries
  - Trader score (consistency × volume)
  - Vault health signals
  - Anomaly flags
  - Seasonal patterns
"""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def build_dataframe(transactions: list[dict]) -> pd.DataFrame:
    """Convert raw Mono transactions to a typed DataFrame."""
    df = pd.DataFrame(transactions)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
    df["type"] = df["type"].str.upper()  # CREDIT / DEBIT
    return df


def daily_summary(df: pd.DataFrame) -> dict:
    """Revenue vs expense breakdown for the most recent day with data."""
    if df.empty:
        return {}
    latest = df["date"].max().date()
    today = df[df["date"].dt.date == latest]
    credits = today[today["type"] == "CREDIT"]["amount"].sum()
    debits = today[today["type"] == "DEBIT"]["amount"].sum()
    return {
        "date": str(latest),
        "revenue": round(float(credits), 2),
        "expenses": round(float(debits), 2),
        "profit": round(float(credits - debits), 2),
    }


def compute_trader_score(df: pd.DataFrame, days: int = 90, savings_balance: float = 0.0) -> float:
    """
    Trader score: 0–100.
    4 components (25 points each): consistency, volume, savings discipline, tenure.
    """
    if df.empty:
        return 0.0
    
    cutoff = datetime.utcnow() - timedelta(days=days)
    window = df[df["date"] >= pd.Timestamp(cutoff)]
    if window.empty:
        return 0.0
        
    # 1. Consistency (25 pts): active days vs expected (e.g. 15 days/month is good)
    active_days = window["date"].dt.date.nunique()
    consistency_ratio = min(active_days / (days * 0.5), 1.0)  # assume trading every other day is max consistency
    consistency_pts = consistency_ratio * 25.0
    
    # 2. Volume (25 pts): log scale capped at 5M
    total_volume = window[window["type"] == "CREDIT"]["amount"].sum()
    volume_ratio = min(np.log1p(total_volume) / np.log1p(5_000_000), 1.0)
    volume_pts = volume_ratio * 25.0
    
    # 3. Savings Discipline (25 pts): ratio of savings balance to 30d revenue
    revenue_30d = df[(df["date"] >= pd.Timestamp(datetime.utcnow() - timedelta(days=30))) & (df["type"] == "CREDIT")]["amount"].sum()
    savings_ratio = min(savings_balance / revenue_30d, 1.0) if revenue_30d > 0 else 0.0
    savings_pts = savings_ratio * 25.0
    
    # 4. Tenure (25 pts): days since first transaction
    first_tx_date = df["date"].min().to_pydatetime()
    tenure_days = (datetime.utcnow() - first_tx_date).days
    tenure_ratio = min(tenure_days / 90.0, 1.0)
    tenure_pts = tenure_ratio * 25.0
    
    score = round(consistency_pts + volume_pts + savings_pts + tenure_pts, 1)
    return score


def vault_health(vault_balances: dict[str, float], revenue_30d: float) -> dict:
    """Flag vaults that are underfunded relative to expected split."""
    signals = {}
    for vault, balance in vault_balances.items():
        expected = revenue_30d * 0.2  # rough 20% baseline
        ratio = balance / expected if expected > 0 else 0
        signals[vault] = {
            "balance": balance,
            "health": "good" if ratio >= 0.8 else "low" if ratio >= 0.4 else "critical",
        }
    return signals


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    """Flag transactions > 2 std deviations from the mean."""
    if df.empty or len(df) < 5:
        return []
    credits = df[df["type"] == "CREDIT"]["amount"]
    mean, std = credits.mean(), credits.std()
    anomalies = df[(df["type"] == "CREDIT") & (df["amount"] > mean + 2 * std)]
    return anomalies[["date", "amount", "narration"]].to_dict("records")


def full_context(transactions: list[dict], vault_balances: dict = None) -> dict:
    """Master function — produces everything the LLM needs in one call."""
    df = build_dataframe(transactions)
    revenue_30d = 0.0
    if not df.empty:
        cutoff = datetime.utcnow() - timedelta(days=30)
        w = df[(df["date"] >= pd.Timestamp(cutoff)) & (df["type"] == "CREDIT")]
        revenue_30d = float(w["amount"].sum())
    return {
        "daily": daily_summary(df),
        "trader_score": compute_trader_score(df),
        "vault_health": vault_health(vault_balances or {}, revenue_30d),
        "anomalies": detect_anomalies(df),
        "revenue_30d": round(revenue_30d, 2),
    }
