# rules.py

from datetime import datetime, timezone, timedelta
from data_loader import load_pep_list, load_ofac_list

# Constants and defaults
HIGH_RISK_COUNTRIES               = {"NG", "IR", "KP", "SY", "VE"}
CTR_THRESHOLD_DEFAULT             = 10_000
EXPOSURE_THRESHOLD_DEFAULT        = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT   = 5
MIN_RETENTION_YEARS_DEFAULT       = 5

# Metadata mapping: rule_name → (regulation_label, short_description)
RULE_META = {
    # AML
    "LargeTxn":               ("AML Section 1", "CTR threshold exceeded"),
    "CIPFailure":             ("AML Section 2", "Customer ID/KYC not completed"),
    "HighRiskCustomer":       ("AML Section 3", "Enhanced due diligence for high-risk customers"),
    "SuspiciousActivity":     ("AML Section 5", "SAR filing required for unusual activity"),
    "SanctionsHit":           ("AML Section 7", "Sanctions & watch-list screening"),
    # BCBS 239
    "MissingField":           ("BCBS 239 Principle 4", "Completeness: no missing fields"),
    "NegativeAmount":         ("BCBS 239 Principle 3", "Accuracy & integrity: no invalid/negative amounts"),
    "StaleData":              ("BCBS 239 Principle 5", "Timeliness: data ≤ 24 h old"),
    "HighCustomerExposure":   ("BCBS 239 Principle 2", "Data architecture: consolidate exposures"),
    # GDPR
    "MissingRetention":       ("GDPR Article 5", "Personal data retention requirement"),
    "RetentionPeriodTooShort":("GDPR Article 5", "Data retained < minimum years"),
    # SOX
    "SoDViolation":           ("SOX Section 404", "Segregation of duties violation"),
    # New PEP & OFAC rules
    "PEPMatch":               ("AML Section 4", "PEP screening"),
    "OFACMatch":              ("AML Section 7", "OFAC sanctions watch-list screening")
}

def evaluate_aml_rules(tx, ctr_threshold=CTR_THRESHOLD_DEFAULT, country_list=HIGH_RISK_COUNTRIES):
    alerts = []
    # Section 1: CTR threshold
    if tx.get("amount", 0) > ctr_threshold:
        alerts.append(("LargeTxn", tx.get("tx_id"), tx.get("amount")))
    # Section 2: CIP/KYC
    if not tx.get("kyc_completed", False):
        alerts.append(("CIPFailure", tx.get("tx_id"), "KYC not completed"))
    # Section 3: High-risk customers
    if tx.get("risk_rating") == "High":
        alerts.append(("HighRiskCustomer", tx.get("tx_id"), tx.get("risk_rating")))
    # Section 7: Static country-based sanctions screening
    if tx.get("sender_country") in country_list or tx.get("receiver_country") in country_list:
        pair = f"{tx.get('sender_country')}→{tx.get('receiver_country')}"
        alerts.append(("SanctionsHit", tx.get("tx_id"), pair))
    return alerts

def evaluate_sar_batch(txs, sar_threshold=SAR_TXN_COUNT_THRESHOLD_DEFAULT):
    alerts = []
    counts = {}
    for tx in txs:
        cid = tx.get("customer_id")
        counts[cid] = counts.get(cid, 0) + 1
    for cid, count in counts.items():
        if count > sar_threshold:
            alerts.append(("SuspiciousActivity", cid, f"{count} transactions"))
    return alerts

def evaluate_bcbs239_batch(txs, exposure_threshold=EXPOSURE_THRESHOLD_DEFAULT):
    alerts = []
    now = datetime.now(timezone.utc)
    required = ["tx_id", "timestamp", "amount", "currency", "customer_id"]
    # Per-transaction checks
    for tx in txs:
        for field in required:
            if not tx.get(field):
                alerts.append(("MissingField", tx.get("tx_id", "<unknown>"), field))
        if tx.get("amount", 0) <= 0:
            alerts.append(("NegativeAmount", tx.get("tx_id", "<unknown>"), tx.get("amount", 0)))
        ts = tx.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            if now - dt > timedelta(hours=24):
                alerts.append(("StaleData", tx.get("tx_id"), ts))
        except:
            alerts.append(("StaleData", tx.get("tx_id", "<unknown>"), ts))
    # Aggregate-level exposure
    exposures = {}
    for tx in txs:
        cid = tx.get("customer_id")
        exposures[cid] = exposures.get(cid, 0) + tx.get("amount", 0)
    for cid, total in exposures.items():
        if total > exposure_threshold:
            alerts.append(("HighCustomerExposure", cid, total))
    return alerts

def evaluate_gdpr_rules(tx, min_retention_years=MIN_RETENTION_YEARS_DEFAULT):
    alerts = []
    if "retention_period" not in tx:
        alerts.append(("MissingRetention", tx.get("tx_id", "<unknown>"), "No retention_period"))
    elif tx.get("retention_period", 0) < min_retention_years:
        alerts.append(("RetentionPeriodTooShort", tx.get("tx_id"), tx.get("retention_period")))
    return alerts

def evaluate_sox_rules(tx):
    alerts = []
    if tx.get("initiator_id") and tx.get("approver_id") \
       and tx["initiator_id"] == tx["approver_id"]:
        alerts.append(("SoDViolation", tx.get("tx_id"), "Initiator equals approver"))
    return alerts

def evaluate_pep_rule(tx, pep_list, enabled=True):
    if not enabled:
        return []
    cid = tx.get("customer_id")
    if cid and cid in pep_list:
        return [("PEPMatch", cid, "Customer is PEP")]
    return []

def evaluate_ofac_rule(tx, ofac_list, enabled=True):
    if not enabled:
        return []
    alerts = []
    acct_s = tx.get("sender_account")
    acct_r = tx.get("receiver_account")
    if acct_s and acct_s in ofac_list:
        alerts.append(("OFACMatch", tx.get("tx_id"), f"Sender {acct_s} on OFAC list"))
    if acct_r and acct_r in ofac_list:
        alerts.append(("OFACMatch", tx.get("tx_id"), f"Receiver {acct_r} on OFAC list"))
    return alerts

def run_compliance_batch(
    txs,
    ctr_threshold=CTR_THRESHOLD_DEFAULT,
    exposure_threshold=EXPOSURE_THRESHOLD_DEFAULT,
    sar_threshold=SAR_TXN_COUNT_THRESHOLD_DEFAULT,
    min_retention_years=MIN_RETENTION_YEARS_DEFAULT,
    enable_pep=True,
    enable_ofac=True
):
    # Load dynamic screening lists
    pep_list  = load_pep_list() if enable_pep else set()
    ofac_list = load_ofac_list() if enable_ofac else set()

    alerts = []
    # Per-transaction AML rules
    for tx in txs:
        alerts.extend(evaluate_aml_rules(tx, ctr_threshold))
    # Batch AML SAR
    alerts.extend(evaluate_sar_batch(txs, sar_threshold))
    # PEP & OFAC rules
    for tx in txs:
        alerts.extend(evaluate_pep_rule(tx, pep_list, enable_pep))
        alerts.extend(evaluate_ofac_rule(tx, ofac_list, enable_ofac))
    # BCBS 239 rules
    alerts.extend(evaluate_bcbs239_batch(txs, exposure_threshold))
    # GDPR & SOX rules
    for tx in txs:
        alerts.extend(evaluate_gdpr_rules(tx, min_retention_years))
        alerts.extend(evaluate_sox_rules(tx))

    return alerts
