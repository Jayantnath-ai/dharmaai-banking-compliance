# rules.py

from datetime import datetime, timezone, timedelta
from data_loader import load_pep_list, load_ofac_list

# Params and thresholds
HIGH_RISK_COUNTRIES             = {"NG","IR","KP","SY","VE"}
CTR_THRESHOLD_DEFAULT           = 10_000
EXPOSURE_THRESHOLD_DEFAULT      = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT = 5
MIN_RETENTION_YEARS_DEFAULT     = 5

# Metadata mapping: rule_name → (regulation_label, short_description)
RULE_META = {
    "LargeTxn":               ("AML Section 1", "CTR threshold exceeded"),
    "CIPFailure":             ("AML Section 2", "Customer KYC not completed"),
    "HighRiskCustomer":       ("AML Section 3", "High-risk customer"),
    "SuspiciousActivity":     ("AML Section 5", "SAR velocity rule"),
    "SanctionsHit":           ("AML Section 7", "Country-based screening"),
    "MissingField":           ("BCBS 239 P4", "Completeness: missing field"),
    "NegativeAmount":         ("BCBS 239 P3", "Accuracy: negative amount"),
    "StaleData":              ("BCBS 239 P5", "Timeliness: >24h old"),
    "HighCustomerExposure":   ("BCBS 239 P2", "Exposure aggregation"),
    "MissingRetention":       ("GDPR Art 5", "Retention missing"),
    "RetentionPeriodTooShort":("GDPR Art 5", "Retention too short"),
    "SoDViolation":           ("SOX 404", "Segregation of duties"),
    "PEPMatch":               ("AML Section 4", "PEP screening"),
    "OFACMatch":              ("AML Section 7", "OFAC screening"),
    "EDDHierarchyFailure":    ("AML Section 4", "Beneficial-owner hierarchy"),
    "EDDFailure":             ("AML Section 4", "Missing source-of-funds")
}

def evaluate_aml_rules(tx, ctr_threshold=CTR_THRESHOLD_DEFAULT):
    alerts = []
    if tx.get("amount",0) > ctr_threshold:
        alerts.append(("LargeTxn", tx.get("tx_id"), tx.get("amount")))
    if not tx.get("kyc_completed",False):
        alerts.append(("CIPFailure", tx.get("tx_id"), "KYC not done"))
    if tx.get("risk_rating") == "High":
        alerts.append(("HighRiskCustomer", tx.get("tx_id"), tx.get("risk_rating")))
    if tx.get("sender_country") in HIGH_RISK_COUNTRIES or tx.get("receiver_country") in HIGH_RISK_COUNTRIES:
        pair = f"{tx.get('sender_country')}→{tx.get('receiver_country')}"
        alerts.append(("SanctionsHit", tx.get("tx_id"), pair))
    return alerts

def evaluate_sar_batch(txs, sar_threshold=SAR_TXN_COUNT_THRESHOLD_DEFAULT):
    counts={}
    alerts=[]
    for tx in txs:
        cid = tx.get("customer_id")
        counts[cid]=counts.get(cid,0)+1
    for cid,count in counts.items():
        if count>sar_threshold:
            alerts.append(("SuspiciousActivity",cid,f"{count} txns"))
    return alerts

def evaluate_bcbs239_batch(txs, exposure_threshold=EXPOSURE_THRESHOLD_DEFAULT):
    alerts=[]
    now=datetime.now(timezone.utc)
    required=["tx_id","timestamp","amount","currency","customer_id"]
    for tx in txs:
        for f in required:
            if not tx.get(f):
                alerts.append(("MissingField",tx.get("tx_id","<unk>"),f))
        if tx.get("amount",0)<=0:
            alerts.append(("NegativeAmount",tx.get("tx_id","<unk>"),tx.get("amount",0)))
        ts=tx.get("timestamp","")
        try:
            dt=datetime.fromisoformat(ts)
            if now-dt>timedelta(hours=24):
                alerts.append(("StaleData",tx.get("tx_id"),ts))
        except:
            alerts.append(("StaleData",tx.get("tx_id","<unk>"),ts))
    exposures={}
    for tx in txs:
        cid=tx.get("customer_id")
        exposures[cid]=exposures.get(cid,0)+tx.get("amount",0)
    for cid,total in exposures.items():
        if total>exposure_threshold:
            alerts.append(("HighCustomerExposure",cid,total))
    return alerts

def evaluate_gdpr_rules(tx, min_retention_years=MIN_RETENTION_YEARS_DEFAULT):
    alerts=[]
    if "retention_period" not in tx:
        alerts.append(("MissingRetention",tx.get("tx_id","<unk>"),"No retention"))
    elif tx.get("retention_period",0)<min_retention_years:
        alerts.append(("RetentionPeriodTooShort",tx.get("tx_id"),tx.get("retention_period")))
    return alerts

def evaluate_sox_rules(tx):
    alerts=[]
    if tx.get("initiator_id") and tx.get("approver_id") and tx["initiator_id"]==tx["approver_id"]:
        alerts.append(("SoDViolation",tx.get("tx_id"),"Initiator==Approver"))
    return alerts

def evaluate_pep_rule(tx,pep_list,enabled=True):
    if not enabled: return []
    cid=tx.get("customer_id")
    return [("PEPMatch",cid,"PEP customer")] if cid in pep_list else []

def evaluate_ofac_rule(tx,ofac_list,enabled=True):
    if not enabled: return []
    alerts=[]
    s=tx.get("sender_account"); r=tx.get("receiver_account")
    if s in ofac_list: alerts.append(("OFACMatch",tx.get("tx_id"),f"Sender {s}"))
    if r in ofac_list: alerts.append(("OFACMatch",tx.get("tx_id"),f"Receiver {r}"))
    return alerts

def evaluate_edd_hierarchy(tx,graph):
    alerts=[]
    cid=tx.get("customer_id")
    for parent,children in graph.items():
        if cid in children and tx.get("risk_rating")=="High":
            alerts.append(("EDDHierarchyFailure",parent,f"High-risk child {cid}"))
    return alerts

def evaluate_edd_sof(tx,require_sof,sof_threshold):
    alerts=[]
    if require_sof and tx.get("purpose_code")== "CASH" and tx.get("amount",0)>sof_threshold:
        if not tx.get("source_of_funds"):
            alerts.append(("EDDFailure",tx.get("tx_id"),f"Missing SOF >{sof_threshold}"))
    return alerts
