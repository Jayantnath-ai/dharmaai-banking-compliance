# rules.py

# Define a list of high-risk country ISO codes
HIGH_RISK_COUNTRIES = {"NG", "IR", "KP", "SY", "VE"}

def evaluate_aml_rules(tx):
    """
    Apply AML “scrolls” against a single transaction record.
    Returns a list of alert tuples: (rule_name, tx_id, detail)
    """
    alerts = []
    # Rule 1: Large transaction > $10,000
    if tx.get("amount", 0) > 10_000:
        alerts.append(("LargeTxn", tx["tx_id"], tx["amount"]))
    # Rule 2: High-risk country involved
    if tx.get("sender_country") in HIGH_RISK_COUNTRIES or tx.get("receiver_country") in HIGH_RISK_COUNTRIES:
        cr = f"{tx['sender_country']}→{tx['receiver_country']}"
        alerts.append(("HighRiskCountry", tx["tx_id"], cr))
    # Rule 3: High-risk customer rating
    if tx.get("risk_rating") == "High":
        alerts.append(("HighRiskCustomer", tx["tx_id"], tx["risk_rating"]))
    return alerts

def run_aml_batch(txs):
    """
    Evaluate a batch of transactions, returning all alerts.
    """
    all_alerts = []
    for tx in txs:
        all_alerts.extend(evaluate_aml_rules(tx))
    return all_alerts
