### rules.py
```python
from datetime import datetime, timezone, timedelta

# AML parameters
HIGH_RISK_COUNTRIES = {"NG", "IR", "KP", "SY", "VE"}
EXPOSURE_THRESHOLD = 100_000  # for BCBS 239 aggregated exposure

# Sanctions list for watch-list screening
SANCTIONS_LIST = {"SY", "IR", "KP"}

# Regulation metadata
RULE_META = {
    # AML Rules
    "LargeTxn":             ("AML Section 1", "CTR threshold > $10 000"),
    "CIPFailure":           ("AML Section 2", "Customer ID/KYC not completed"),
    "HighRiskCustomer":     ("AML Section 3", "Enhanced due diligence for high-risk customers"),
    "SuspiciousActivity":   ("AML Section 5", "Unusual transaction pattern detected"),
    "SanctionsHit":         ("AML Section 7", "Sanctions or watch-list screening hit"),
    # BCBS 239 Principles
    "MissingField":         ("BCBS 239 Principle 4", "Completeness: no missing fields"),
    "NegativeAmount":       ("BCBS 239 Principle 3", "Accuracy & integrity: no invalid/negative amounts"),
    "StaleData":            ("BCBS 239 Principle 5", "Timeliness: data ≤ 24 h old"),
    "HighCustomerExposure": ("BCBS 239 Principle 2", "Data architecture: consolidate exposures")
}

# AML rule definitions

def evaluate_aml_rules(tx):
    alerts = []
    # Section 1: Large transactions
    if tx.get("amount", 0) > 10_000:
        alerts.append(("LargeTxn", tx["tx_id"], tx["amount"]))
    # Section 2: Customer Identification / KYC
    if not tx.get("kyc_completed", False):
        alerts.append(("CIPFailure", tx["tx_id"], "KYC incomplete"))
    # Section 3: High-risk customer
    if tx.get("risk_rating") == "High":
        alerts.append(("HighRiskCustomer", tx["tx_id"], tx["risk_rating"]))
    # Section 5: Suspicious activity (e.g., large transfers)
    if tx.get("purpose_code") == "TRANSFER" and tx.get("amount", 0) > 20_000:
        alerts.append(("SuspiciousActivity", tx["tx_id"], tx["amount"]))
    # Section 7: Sanctions screening
    if tx.get("sender_country") in SANCTIONS_LIST or tx.get("receiver_country") in SANCTIONS_LIST:
        country_pair = f"{tx['sender_country']}→{tx['receiver_country']}"
        alerts.append(("SanctionsHit", tx["tx_id"], country_pair))
    return alerts

# BCBS 239 rule definitions

def evaluate_bcbs239_batch(txs):
    alerts = []
    now = datetime.now(timezone.utc)
    required = ["tx_id", "timestamp", "amount", "currency", "customer_id"]

    # Per-transaction checks
    for tx in txs:
        # Missing or empty fields
        for field in required:
            if not tx.get(field):
                alerts.append(("MissingField", tx.get("tx_id", "<unknown>"), field))
        # Amount must be positive
        if tx.get("amount", 0) <= 0:
            alerts.append(("NegativeAmount", tx["tx_id"], tx.get("amount")))
        # Freshness of data
        try:
            ts = datetime.fromisoformat(tx["timestamp"])
            if now - ts > timedelta(hours=24):
                alerts.append(("StaleData", tx["tx_id"], tx["timestamp"]))
        except Exception:
            alerts.append(("StaleData", tx.get("tx_id", "<unknown>"), tx.get("timestamp")))

    # Aggregate-level exposure check
    exposures = {}
    for tx in txs:
        cid = tx.get("customer_id")
        exposures[cid] = exposures.get(cid, 0) + tx.get("amount", 0)
    for cid, total in exposures.items():
        if total > EXPOSURE_THRESHOLD:
            alerts.append(("HighCustomerExposure", cid, total))

    return alerts

# Combined compliance run

def run_compliance_batch(txs):
    """
    Combined AML + BCBS 239 compliance checks.
    Returns list of tuples: (rule_name, entity, detail).
    """
    alerts = []
    for tx in txs:
        alerts.extend(evaluate_aml_rules(tx))
    alerts.extend(evaluate_bcbs239_batch(txs))
    return alerts
```  

### app.py
```python
import streamlit as st
from faker import Faker
import uuid
from random import gauss, choice
from collections import Counter
import csv, io

from rules import run_compliance_batch, RULE_META

fake = Faker()

# --- Mock Customer Profiles ---
def gen_customer():
    return {
        "customer_id": str(uuid.uuid4()),
        "risk_rating": choice(["Low","Medium","High"]),
        "kyc_completed": choice([True, False])
    }
CUSTOMERS = [gen_customer() for _ in range(200)]
CUST_MAP = {c["customer_id"]: c for c in CUSTOMERS}

# --- Transaction Generator ---
def gen_transaction():
    cid = choice(list(CUST_MAP.keys()))
    profile = CUST_MAP[cid]
    return {
        "tx_id": str(uuid.uuid4()),
        "timestamp": fake.iso8601(),
        "amount": round(abs(gauss(5000, 8000)), 2),
        "currency": "USD",
        "sender_account": fake.bban(),
        "receiver_account": fake.bban(),
        "sender_country": fake.country_code(),
        "receiver_country": fake.country_code(),
        "purpose_code": choice(["CASH","PAYMENT","TRANSFER"]),
        "customer_id": cid,
        "risk_rating": profile["risk_rating"],
        "kyc_completed": profile["kyc_completed"]
    }

# --- Streamlit UI ---
st.title("🏦 DharmaAI Compliance Demo (AML + BCBS 239)")

if st.button("Run 200 Mock TX & Full Compliance Checks"):
    txs = [gen_transaction() for _ in range(200)]
    raw_alerts = run_compliance_batch(txs)

    # Build audit-trail records with regulation info
    tx_map = {tx["tx_id"]: tx for tx in txs}
    records = []
    for rule, entity, detail in raw_alerts:
        reg_label, reg_desc = RULE_META.get(rule, ("Unknown", ""))
        ts = tx_map.get(entity, {}).get("timestamp", "")
        records.append({
            "rule": rule,
            "regulation": reg_label,
            "description": reg_desc,
            "entity": entity,
            "detail": detail,
            "timestamp": ts
        })

    # Metrics
    st.subheader("🔍 Summary")
    st.write(f"- Processed **{len(txs)}** transactions")
    st.write(f"- Generated **{len(records)}** alerts")
    st.write("**Alerts by rule:**")
    for rule, cnt in Counter(r["rule"] for r in records).items():
        st.write(f"- {rule}: {cnt}")

    # Alert table + CSV download
    if records:
        st.subheader("⚠️ Alert Audit Trail")
        st.table(records)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        st.download_button(
            label="Download Alerts as CSV",
            data=buf.getvalue(),
            file_name="compliance_alerts.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ No alerts—all checks passed")
