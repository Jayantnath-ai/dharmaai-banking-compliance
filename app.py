import streamlit as st
import json
from rules import *  # our durable-rules ruleset

st.title("🏦 DharmaAI AML Compliance Demo")

if st.button("Run Mock Data Through Rules"):
    txs = json.load(open("transactions.json"))
    for tx in txs[:100]:  # sample first 100 for speed
        post('aml', tx)
    st.success("Processed 100 transactions. Check console for alerts.")
