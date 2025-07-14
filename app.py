import streamlit as st
from faker import Faker
import uuid
from random import gauss, choice
from rules import run_aml_batch

fake = Faker()

def gen_transaction():
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
        "customer_risk_score": choice([20, 40, 60, 80, 95])
    }

st.title("🏦 DharmaAI AML Compliance Demo")

if st.button("Run 100 Mock TX through Rules"):
    txs = [gen_transaction() for _ in range(100)]
    alerts = run_aml_batch(txs)

    if alerts:
        st.error(f"⚠️ {len(alerts)} alerts generated")
        for rule, tx_id, detail in alerts:
            st.write(f"- **{rule}** on TX {tx_id}: {detail}")
    else:
        st.success("✅ No alerts—all transactions passed")
