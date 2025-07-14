# rules.py

def evaluate_aml_rules(tx):
    """
    Apply AML “scrolls” against a single transaction record.
    Returns a list of alert tuples: (rule_name, tx_id, detail)
    """
    alerts = []
    # Rule 1: Large transaction > $10,000
    if tx.get("amount", 0) > 10_000:
        alerts.append(("LargeTxn", tx["tx_id"], tx["amount"]))
    # Rule 2: High-risk customer score > 80
    if tx.get("customer_risk_score", 0) > 80:
        alerts.append(("HighRiskCustomer", tx["tx_id"], tx["customer_risk_score"]))
    # (You can add more rules here in the same pattern)
    return alerts

def run_aml_batch(txs):
    """
    Evaluate a batch of transactions, returning all alerts.
    """
    all_alerts = []
    for tx in txs:
        all_alerts.extend(evaluate_aml_rules(tx))
    return all_alerts
