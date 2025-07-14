# rules.py
from datetime import datetime, timezone, timedelta

# AML parameters
HIGH_RISK_COUNTRIES = {"NG", "IR", "KP", "SY", "VE"}
EXPOSURE_THRESHOLD = 100_000  # for BCBS 239 aggregated exposure

def evaluate_aml_rules(tx):
    alerts = []
    if tx.get("amount", 0) > 10_000:
        alerts.append(("LargeTxn", tx["tx_id"], tx["amount"]))
    if tx.get("sender_country") in HIGH_RISK_COUNTRIES \
       or tx.get("receiver_country") in HIGH_RISK_COUNTRIES:
        cr = f"{tx['sender_country']}→{tx['receiver_country']}"
        alerts.append(("HighRiskCountry", tx["tx_id"], cr))
    if tx.get("risk_rating") == "High":
        alerts.append(("HighRiskCustomer", tx["tx_id"], tx["risk_rating"]))
    return alerts

def evaluate_bcbs239_batch(txs):
    alerts = []
    now = datetime.now(timezone.utc)

    # Per-transaction checks
    required = ["tx_id", "timestamp", "amount", "currency", "customer_id"]
    for tx in txs:
        # 1. MissingField
        for field in required:
            if not tx.get(field):
                alerts.append(("MissingField", tx.get("tx_id", "<unknown>"), field))
        # 2. NegativeAmount
        if tx.get("amount", 0) <= 0:
            alerts.append(("NegativeAmount", tx["tx_id"], tx.get("amount")))
        # 3. StaleData
        try:
            ts = datetime.fromisoformat(tx["timestamp"])
            if now - ts > timedelta(hours=24):
                alerts.append(("StaleData", tx["tx_id"], tx["timestamp"]))
        except Exception:
            # malformed timestamp
            alerts.append(("StaleData", tx.get("tx_id", "<unknown>"), tx.get("timestamp")))

    # 4. HighCustomerExposure (aggregate)
    exposures = {}
    for tx in txs:
        cid = tx.get("customer_id")
        exposures[cid] = exposures.get(cid, 0) + tx.get("amount", 0)
    for cid, total in exposures.items():
        if total > EXPOSURE_THRESHOLD:
            alerts.append(("HighCustomerExposure", cid, total))

    return alerts

def run_compliance_batch(txs):
    """
    Combined AML + BCBS 239 compliance checks.
    """
    alerts = []
    # AML alerts
    for tx in txs:
        alerts.extend(evaluate_aml_rules(tx))
    # BCBS 239 alerts
    alerts.extend(evaluate_bcbs239_batch(txs))
    return alerts
