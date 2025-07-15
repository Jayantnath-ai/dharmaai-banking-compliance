# ui.py - All Streamlit layout, charts, tables and download
import streamlit as st
import altair as alt
import pandas as pd
import csv, io
from collections import Counter
from datetime import datetime

def configure_page():
    st.set_page_config(
        page_title="DharmaAI Banking Compliance",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown("## 🏦 DharmaAI Banking Compliance Demo", unsafe_allow_html=True)
    st.write("---")

def sidebar_settings(
    RULE_META, STRUCTURED_EXT, UNSTRUCTURED_EXT, DATE_FILTER_DEFAULT,
    CTR_DEFAULT, EXPOSURE_DEFAULT, SAR_DEFAULT, RETENTION_DEFAULT
):
    st.sidebar.title("⚙️ Settings")
    st.sidebar.markdown("### Data Source")
    uploaded_file = st.sidebar.file_uploader(
        "Upload transactions file",
        type=list(STRUCTURED_EXT.union(UNSTRUCTURED_EXT)),
        help="Structured CSV/JSON/XLSX or plain text (.txt)"
    )
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    all_rules = list(RULE_META.keys())
    selected_rules = st.sidebar.multiselect("Rules", options=all_rules, default=all_rules)
    all_regs = sorted({meta[0] for meta in RULE_META.values()})
    selected_regs = st.sidebar.multiselect("Regulations", options=all_regs, default=all_regs)
    date_filter = st.sidebar.date_input("From Date", value=DATE_FILTER_DEFAULT)
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Thresholds")
    ctr_threshold = st.sidebar.number_input("CTR threshold ($)",       min_value=1, value=CTR_DEFAULT)
    exposure_threshold = st.sidebar.number_input("Exposure threshold ($)",min_value=1, value=EXPOSURE_DEFAULT)
    sar_threshold = st.sidebar.number_input("SAR txn threshold",      min_value=1, value=SAR_DEFAULT)
    min_retention_years = st.sidebar.number_input("Min retention (yrs)",min_value=1, value=RETENTION_DEFAULT)

    return (
        uploaded_file, selected_rules, selected_regs, date_filter,
        ctr_threshold, exposure_threshold, sar_threshold, min_retention_years
    )

def show_metrics(txs, filtered):
    tx_count    = len(txs)
    alert_count = len(filtered)
    unique_rules= len({r["rule"] for r in filtered})
    c1, c2, c3 = st.columns(3)
    c1.metric("Transactions",   tx_count)
    c2.metric("Alerts",         alert_count)
    c3.metric("Unique Rules",   unique_rules)

def show_chart(filtered):
    counts = Counter(r["rule"] for r in filtered)
    df = pd.DataFrame.from_dict(counts, orient='index', columns=['count']).reset_index()
    df.columns = ['rule','count']
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('rule', sort='-y'),
        y='count',
        tooltip=['rule','count']
    ).properties(width='container', height=300)
    st.altair_chart(chart, use_container_width=True)

def show_table_and_download(filtered):
    st.subheader("⚠️ Alert Audit Trail")
    st.dataframe(filtered, height=400)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=filtered[0].keys())
    writer.writeheader()
    writer.writerows(filtered)
    st.download_button(
        "Download Alerts as CSV", data=buf.getvalue(),
        file_name="compliance_alerts.csv", mime="text/csv"
    )
