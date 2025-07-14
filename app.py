import streamlit as st
from faker import Faker
import uuid
from random import gauss, choice
from collections import Counter
import csv, io

from rules import run_aml_batch

fake = Faker()

# --- Mock Customer Profiles ---
def gen_customer():
    return {
        "customer_id": str(uuid.uuid4()),
        "risk_rating": choice(["Low", "Medium", "High"])
    }

# Build an in-memory list of profiles
CUSTOMERS = [gen_customer() for _ in range(200)]
CUST_MAP = {c["customer_id"]: c["risk_rating"] for c in CUSTOMERS}

# --- Transaction Generator ---
def gen_transaction():
    # pick a random customer and embed its rating
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
        "purpose_code": choice(["CASH", "PAYMENT", "TRANSFER"]),
        "customer_id": cid,
        "risk_rating": CUST_MAP[cid]
    }

# --- Streamlit UI ---
st.title("🏦 DharmaAI AML Compliance Demo")

if st.button("Run 200 Mock TX through Rules"):
    txs = [gen_transaction() for _ in range(200)]
    alerts = run_aml_batch(txs)

    # Build audit-trail records
    tx_map = {tx["tx_id"]: tx for tx in txs}
    records = []
    for rule, tx_id, detail in alerts:
        tx = tx_map[tx_id]
        records.append({
            "rule": rule,
            "tx_id": tx_id,
            "detail": detail,
            "timestamp": tx["timestamp"]
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

    # Alert table
    if records:
        st.subheader("⚠️ Alert Audit Trail")
        st.table(records)

        # CSV download
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["rule","tx_id","detail","timestamp"])
        writer.writeheader()
        writer.writerows(records)
        csv_data = buf.getvalue()

        st.download_button(
            label="Download Alerts as CSV",
            data=csv_data,
            file_name="aml_alerts.csv",
            mime="text/csv"
        )
    else:
        st.success("✅ No alerts—all transactions passed")
