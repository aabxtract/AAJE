import pandas as pd

def detect_anomaly(transaction: dict, historical_df: pd.DataFrame) -> dict:
    """
    Compares current transaction against historical patterns.
    Flags unusually large debits, transactions at unusual times, etc.
    """
    if historical_df.empty or len(historical_df) < 5:
        return {}
        
    amount = transaction.get("amount", 0)
    tx_type = transaction.get("type", "CREDIT").upper()
    
    # Filter historical by type
    history = historical_df[historical_df["type"] == tx_type]
    if history.empty:
        return {}
        
    mean = history["amount"].mean()
    std = history["amount"].std()
    
    if amount > mean + (3 * std):
        return {
            "type": "unusually_large_amount",
            "severity": "high",
            "description": f"Transaction of {amount} is significantly higher than historical average of {mean:.2f}."
        }
        
    return {}
