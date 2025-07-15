import streamlit as st
from faker import Faker
import uuid
from random import gauss, choice
from datetime import datetime, date
from collections import Counter
import pandas as pd
import csv, io

from rules import run_compliance_batch, RULE_META

fake = Faker()

# --- Sidebar: Data Source & Filters ---
st.sidebar.header("Data Source")
uploaded_file = st.sidebar.file_uploader(
    "Upload transactions file",
    type=['csv', 'json', 'xlsx'],
    help="Accepts CSV, JSON, or Excel files. If none uploaded, mock data will be used."
)

st.sidebar.header("Filter Controls")
all_rules = list(RULE_META.keys())
selected_rules = st.sidebar.multiselect("Rules", options=all_rules, default=all_rules)
all_regs = sorted({meta[0] for meta in RULE_META.values()})
selected_regs = st.sidebar.multiselect("Regulations", options=all_regs, default=all_regs)

date_filter = st.sidebar.date_input("From Date", value=date(1970, 1, 1))

st.sidebar.header("Threshold Parameters")
ctr_threshold        = st.sidebar.number_input("CTR threshold ($)",       min_value=1,    value=10000)
exposure_threshold   = st.sidebar.number_input("Exposure threshold ($)",  min_value=1,    value=100000)
sar_threshold        = st.sidebar.number_input("SAR txn count threshold", min_value=1,    value=5)
min_retention_years  = st.sidebar.number_input("Min retention (yrs)",     min_value=1,    value=5)

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
        # GDPR & SOX fields
        "retention_period": choice([1, 3, 5, 7, 10]),
        "initiator_id":     fake.bothify("EMP-####"),
        "approver_id":      fake.bothify("EMP-####")
    }

# --- App UI ---
st.title("🏦 DharmaAI Banking Compliance Demo (AML, BCBS, GDPR, SOX)")

if st.button("Run Compliance Checks"):
    # Load data from upload or generate mock
    if uploaded_file:
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            elif uploaded_file.name.endswith('.json'):
                df = pd.read_json(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            txs = df.to_dict(orient='records')
        except Exception as e:
            st.error(f"Error reading file: {e}")
            st.stop()
    else:
        txs = [gen_transaction() for _ in range(200)]

    # Run compliance rules
    raw_alerts = run_compliance_batch(
        txs,
        ctr_threshold=ctr_threshold,
        exposure_threshold=exposure_threshold,
        sar_threshold=sar_threshold,
        min_retention_years=min_retention_years
    )

    # Build audit-trail records
    tx_map = {tx.get("tx_id", idx): tx for idx, tx in enumerate(txs)}
    records = []
    for rule, entity, detail in raw_alerts:
        reg_label, reg_desc = RULE_META.get(rule, ("Unknown", ""))
        tx = tx_map.get(entity, {})
        ts = tx.get("timestamp", "")
        rec_date = None
        if ts:
            try:
                rec_date = datetime.fromisoformat(ts).date()
            except Exception:
                rec_date = None
        records.append({
            "rule":        rule,
            "regulation":  reg_label,
            "description": reg_desc,
            "entity":      entity,
            "detail":      detail,
            "timestamp":   ts,
            "date":        rec_date
        })

    # Apply filters
    filtered = [
        r for r in records
        if r["rule"] in selected_rules
        and r["regulation"] in selected_regs
        and r["date"] and r["date"] >= date_filter
    ]

    # Metrics
    st.subheader("🔍 Summary")
    st.write(f"- Records processed: **{len(txs)}**")
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
        writer = csv.DictWriter(
            buf,
            fieldnames=["rule","regulation","description","entity","detail","timestamp","date"]
        )
        writer.writeheader()
        writer.writerows(filtered)

        st.download_button(
            label="Download Alerts as CSV",
            data=buf.getvalue(),
            file_name="compliance_alerts.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ No alerts match the filters")
