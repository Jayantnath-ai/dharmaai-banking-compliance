import streamlit as st
from faker import Faker
import uuid
from random import gauss, choice
from collections import Counter
import csv, io

from rules import run_compliance_batch, RULE_META

fake = Faker()

# --- Mock customer setup ---
def gen_customer():
    return {"customer_id": str(uuid.uuid4()), "risk_rating": choice(["Low","Medium","High"])}
CUSTOMERS = [gen_customer() for _ in range(200)]
CUST_MAP = {c["customer_id"]: c["risk_rating"] for c in CUSTOMERS}

# --- Transaction generator ---
def gen_transaction():
    cid = choice(list(CUST_MAP.keys()))
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
        "risk_rating": CUST_MAP[cid]
    }

# --- UI ---
st.title("🏦 DharmaAI Compliance Demo (AML + BCBS 239)")

if st.button("Run 200 Mock TX & BCBS 239 Checks"):
    txs = [gen_transaction() for _ in range(200)]
    raw_alerts = run_compliance_batch(txs)

    # Build audit-trail records with regulation info
    tx_map = {tx["tx_id"]: tx for tx in txs}
    records = []
    for rule, entity, detail in raw_alerts:
        reg_label, reg_desc = RULE_META.get(rule, ("Unknown",""))
        # Determine timestamp for this alert (if per-tx)
        ts = tx_map.get(entity, {}).get("timestamp", "")
        records.append({
            "rule": rule,
            "regulation": f"{reg_label}",
            "description": reg_desc,
            "entity": entity,
            "detail": detail,
            "timestamp": ts
        })

    # Metrics
    total_tx = len(txs)
    total_alerts = len(records)
    counts = Counter(r["rule"] for r in records)

    st.subheader("🔍 Summary")
    st.write(f"- Processed **{total_tx}** transactions")
    st.write(f"- Generated **{total_alerts}** alerts")
    st.write("**Alerts by rule:**")
    for rule, cnt in counts.items():
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
