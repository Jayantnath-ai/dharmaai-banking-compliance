from datetime import datetime, timezone, timedelta

# Metadata mapping: rule_name → (regulation_label, short_description)
RULE_META = {
    # AML
    "LargeTxn":             ("AML Section 1", "CTR threshold exceeded"),
    "CIPFailure":           ("AML Section 2", "Customer ID/KYC not completed"),
    "HighRiskCustomer":     ("AML Section 3", "Enhanced due diligence for high-risk customers"),
    "SuspiciousActivity":   ("AML Section 5", "SAR filing required for unusual activity"),
    "SanctionsHit":         ("AML Section 7", "Sanctions & watch-list screening"),
    # BCBS 239
    "MissingField":         ("BCBS 239 Principle 4", "Completeness: no missing fields"),
    "NegativeAmount":       ("BCBS 239 Principle 3", "Accuracy & integrity: no invalid/negative amounts"),
    "StaleData":            ("BCBS 239 Principle 5", "Timeliness: data ≤ 24 h old"),
    "HighCustomerExposure": ("BCBS 239 Principle 2", "Data architecture: consolidate exposures"),
    # GDPR
    "MissingRetention":     ("GDPR Article 5", "Personal data retention requirement"),
    "RetentionPeriodTooShort": ("GDPR Article 5", "Data retained < minimum years"),
    # SOX
    "SoDViolation":         ("SOX Section 404", "Segregation of duties violation")
}

# Default thresholds (will be overridden by parameters)
CTR_THRESHOLD_DEFAULT            = 10_000
EXPOSURE_THRESHOLD_DEFAULT       = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT  = 5
MIN_RETENTION_YEARS_DEFAULT      = 5

# Static reference data
SANCTIONS_LIST = {"IR", "KP", "SY", "VE"}

# ---- AML rules ----
def evaluate_aml_rules(tx, ctr_threshold, sanctions_list):
    alerts = []
    # Section 1: CTR
    if tx.get("amount", 0) > ctr_threshold:
        alerts.append(("LargeTxn", tx["tx_id"], tx["amount"]))
    # Section 2: CIP/KYC
    if not tx.get("kyc_completed"):
        alerts.append(("CIPFailure", tx.get("tx_id", "<unknown>"), "KYC not completed"))
    # Section 3: High-risk customers
    if tx.get("risk_rating") == "High":
        alerts.append(("HighRiskCustomer", tx["tx_id"], tx["risk_rating"]))
    # Section 7: Sanctions screening
    if tx.get("sender_country") in sanctions_list or tx.get("receiver_country") in sanctions_list:
        pair = f"{tx['sender_country']}→{tx['receiver_country']}"
        alerts.append(("SanctionsHit", tx["tx_id"], pair))
    return alerts

def evaluate_sar_batch(txs, sar_threshold):
    alerts = []
    counts = {}
    for tx in txs:
        cid = tx.get("customer_id")
        counts[cid] = counts.get(cid, 0) + 1
    for cid, count in counts.items():
        if count > sar_threshold:
            alerts.append(("SuspiciousActivity", cid, f"{count} transactions"))
    return alerts

# ---- BCBS 239 rules ----
def evaluate_bcbs239_batch(txs, exposure_threshold):
    alerts = []
    now = datetime.now(timezone.utc)
    required = ["tx_id", "timestamp", "amount", "currency", "customer_id"]
    for tx in txs:
        # MissingField
        for field in required:
            if not tx.get(field):
                alerts.append(("MissingField", tx.get("tx_id", "<unknown>"), field))
        # NegativeAmount
        if tx.get("amount", 0) <= 0:
            alerts.append(("NegativeAmount", tx.get("tx_id", "<unknown>"), tx.get("amount")))
        # StaleData
        try:
            ts = datetime.fromisoformat(tx["timestamp"])
            if now - ts > timedelta(hours=24):
                alerts.append(("StaleData", tx["tx_id"], tx["timestamp"]))
        except Exception:
            alerts.append(("StaleData", tx.get("tx_id", "<unknown>"), tx.get("timestamp")))
    # HighCustomerExposure
    exposures = {}
    for tx in txs:
        cid = tx.get("customer_id")
        exposures[cid] = exposures.get(cid, 0) + tx.get("amount", 0)
    for cid, total in exposures.items():
        if total > exposure_threshold:
            alerts.append(("HighCustomerExposure", cid, total))
    return alerts

# ---- GDPR rules ----
def evaluate_gdpr_rules(tx, min_retention_years):
    alerts = []
    if "retention_period" not in tx:
        alerts.append(("MissingRetention", tx.get("tx_id", "<unknown>"), "No retention_period"))
    else:
        if tx["retention_period"] < min_retention_years:
            alerts.append(("RetentionPeriodTooShort", tx["tx_id"], tx["retention_period"]))
    return alerts

# ---- SOX rules ----
def evaluate_sox_rules(tx):
    alerts = []
    if tx.get("initiator_id") == tx.get("approver_id"):
        alerts.append(("SoDViolation", tx["tx_id"], "Initiator == Approver"))
    return alerts

# ---- Orchestrator ----
def run_compliance_batch(
    txs,
    ctr_threshold=CTR_THRESHOLD_DEFAULT,
    exposure_threshold=EXPOSURE_THRESHOLD_DEFAULT,
    sar_threshold=SAR_TXN_COUNT_THRESHOLD_DEFAULT,
    min_retention_years=MIN_RETENTION_YEARS_DEFAULT
):
    alerts = []
    # AML per‐tx
    for tx in txs:
        alerts.extend(evaluate_aml_rules(tx, ctr_threshold, SANCTIONS_LIST))
    # AML batch (SAR)
    alerts.extend(evaluate_sar_batch(txs, sar_threshold))
    # BCBS 239
    alerts.extend(evaluate_bcbs239_batch(txs, exposure_threshold))
    # GDPR & SOX
    for tx in txs:
        alerts.extend(evaluate_gdpr_rules(tx, min_retention_years))
        alerts.extend(evaluate_sox_rules(tx))
    return alerts
