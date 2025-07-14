import streamlit as st
from faker import Faker
import uuid
from random import gauss, choice
from datetime import datetime
from collections import Counter
import csv, io

from rules import run_compliance_batch, RULE_META

fake = Faker()

# --- Sidebar: Filters & Parameters ---
st.sidebar.header("Filter Controls")
all_rules = list(RULE_META.keys())
selected_rules = st.sidebar.multiselect("Rules", options=all_rules, default=all_rules)
all_regs = sorted({meta[0] for meta in RULE_META.values()})
selected_regs = st.sidebar.multiselect("Regulations", options=all_regs, default=all_regs)
date_filter = st.sidebar.date_input("From Date", value=datetime.now().date())

st.sidebar.header("Threshold Parameters")
ctr_threshold        = st.sidebar.number_input("CTR threshold ($)",       min_value=1, value=10000)
exposure_threshold   = st.sidebar.number_input("Exposure threshold ($)",  min_value=1, value=100000)
sar_threshold        = st.sidebar.number_input("SAR txn count threshold", min_value=1, value=5)
min_retention_years  = st.sidebar.number_input("Min retention (yrs)",     min_value=1, value=5)

# --- Mock Data Generators ---
def gen_customer():
    return {
        "customer_id": str(uuid.uuid4()),
        "risk_rating": choice(["Low", "Medium", "High"]),
        "kyc_completed": choice([True, False])
    }

CUSTOMERS = [gen_customer() for _ in range(200)]
CUST_MAP    = {c["customer_id"]: c for c in CUSTOMERS}

def gen_transaction():
    cid  = choice(list(CUST_MAP.keys()))
    cust = CUST_MAP[cid]
    return {
        "tx_id":           str(uuid.uuid4()),
        "timestamp":       fake.iso8601(),
        "amount":          round(abs(gauss(5000, 8000)), 2),
        "currency":        "USD",
        "sender_account":  fake.bban(),
        "receiver_account":fake.bban(),
        "sender_country":  fake.country_code(),
        "receiver_country":fake.country_code(),
        "purpose_code":    choice(["CASH","PAYMENT","TRANSFER"]),
        "customer_id":     cid,
        "risk_rating":     cust["risk_rating"],
        "kyc_completed":   cust["kyc_completed"],
        # Fields for GDPR & SOX
        "retention_period": choice([1,3,5,7,10]),  # years
        "initiator_id":     fake.bothify("EMP-####"),
        "approver_id":      fake.bothify("EMP-####")
    }

# --- App UI ---
st.title("🏦 DharmaAI Banking Compliance Demo (AML, BCBS, GDPR, SOX)")

if st.button("Run Compliance Checks"):
    txs = [gen_transaction() for _ in range(200)]
    raw_alerts = run_compliance_batch(
        txs,
        ctr_threshold=ctr_threshold,
        exposure_threshold=exposure_threshold,
        sar_threshold=sar_threshold,
        min_retention_years=min_retention_years
    )

    # Build full audit-trail records
    tx_map = {tx["tx_id"]: tx for tx in txs}
    records = []
    for rule, entity, detail in raw_alerts:
        reg_label, reg_desc = RULE_META.get(rule, ("Unknown",""))
        ts = tx_map.get(entity, {}).get("timestamp", "")
        rec_date = datetime.fromisoformat(ts).date() if ts else None
        records.append({
            "rule":       rule,
            "regulation": reg_label,
            "description":reg_desc,
            "entity":     entity,
            "detail":     detail,
            "timestamp":  ts,
            "date":       rec_date
        })

    # Apply filters
    filtered = [
        r for r in records
        if r["rule"] in selected_rules
        and r["regulation"] in selected_regs
        and (r["date"] and r["date"] >= date_filter)
    ]

    # Metrics
    st.subheader("🔍 Summary")
    st.write(f"- Processed **{len(txs)}** transactions")
    st.write(f"- Alerts (filtered): **{len(filtered)}**")
    counts = Counter(r["rule"] for r in filtered)
    st.write("**Alerts by rule:**")
    for rule, cnt in counts.items():
        st.write(f"- {rule}: {cnt}")

    # Display & download
    if filtered:
        st.subheader("⚠️ Alert Audit Trail")
        st.table(filtered)
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["rule","regulation","description","entity","detail","timestamp"])
        writer.writeheader()
        writer.writerows(filtered)
        st.download_button("Download Alerts as CSV", buf.getvalue(), "compliance_alerts.csv", "text/csv")
    else:
        st.success("✅ No alerts match the filters")
