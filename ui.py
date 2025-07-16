import streamlit as st
import altair as alt
import pandas as pd
import csv, io
from collections import Counter
from datetime import datetime

def configure_page():
    st.set_page_config(
        page_title="DharmaAI Compliance",
        page_icon="🏦",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.markdown("## 🏦 DharmaAI Compliance Demo", unsafe_allow_html=True)
    st.write("---")

def sidebar_settings(
    RULE_META,
    structured_ext,
    unstructured_ext,
    date_filter_default,
    ctr_default,
    exposure_default,
    sar_default,
    retention_default,
    velocity_default,
    velocity_window_default,
    geojump_window_default
):
    st.sidebar.title("⚙️ Settings")

    st.sidebar.markdown("### Data Source")
    uploaded_file = st.sidebar.file_uploader(
        "Upload transactions file",
        type=list(structured_ext.union(unstructured_ext)),
        help="Structured CSV/JSON/XLSX or plain-text (.txt)"
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Filters")
    all_rules = list(RULE_META.keys())
    selected_rules = st.sidebar.multiselect("Rules", options=all_rules, default=all_rules)
    all_regs = sorted({meta[0] for meta in RULE_META.values()})
    selected_regs = st.sidebar.multiselect("Regulations", options=all_regs, default=all_regs)
    date_filter = st.sidebar.date_input("From Date", value=date_filter_default)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Thresholds")
    ctr_threshold       = st.sidebar.number_input("CTR threshold ($)",       min_value=1, value=ctr_default)
    exposure_threshold  = st.sidebar.number_input("Exposure threshold ($)",  min_value=1, value=exposure_default)
    sar_threshold       = st.sidebar.number_input("SAR txn threshold",       min_value=1, value=sar_default)
    min_retention_years = st.sidebar.number_input("Min retention (yrs)",     min_value=1, value=retention_default)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Optional Screenings")
    enable_pep  = st.sidebar.checkbox("Enable PEP Screening", value=True)
    enable_ofac = st.sidebar.checkbox("Enable OFAC Screening", value=True)

    st.sidebar.markdown("---")
    st.sidebar.markdown("### EDD Settings")
    ownership_file = st.sidebar.file_uploader(
        "Upload ownership graph (CSV)",
        type=['csv'],
        help="Columns: parent_id, child_id"
    )
    require_sof = st.sidebar.checkbox(
        "Require source-of-funds for large CASH txns",
        value=True
    )
    sof_threshold = st.sidebar.number_input(
        "SOF Amount Threshold ($)",
        min_value=0,
        value=10000
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown("### Monitoring Settings")
    velocity_threshold      = st.sidebar.number_input(
        "Velocity txns threshold (M)", min_value=1, value=velocity_default
    )
    velocity_window_minutes = st.sidebar.number_input(
        "Velocity window (minutes N)", min_value=1, value=velocity_window_default
    )
    geojump_window_minutes  = st.sidebar.number_input(
        "Geo-jump time window (minutes T)", min_value=1, value=geojump_window_default
    )

    return (
        uploaded_file,
        selected_rules,
        selected_regs,
        date_filter,
        ctr_threshold,
        exposure_threshold,
        sar_threshold,
        min_retention_years,
        enable_pep,
        enable_ofac,
        ownership_file,
        require_sof,
        sof_threshold,
        velocity_threshold,
        velocity_window_minutes,
        geojump_window_minutes
    )

def show_metrics(txs, filtered):
    tx_count     = len(txs)
    alert_count  = len(filtered)
    unique_rules = len({r["rule"] for r in filtered})
    col1, col2, col3 = st.columns(3)
    col1.metric("Transactions",   tx_count)
    col2.metric("Alerts",         alert_count)
    col3.metric("Unique Rules",   unique_rules)

def show_chart(filtered):
    counts = Counter(r["rule"] for r in filtered)
    df = pd.DataFrame.from_dict(counts, orient='index', columns=['count']).reset_index()
    df.columns = ['rule', 'count']
    chart = alt.Chart(df).mark_bar().encode(
        x=alt.X('rule', sort='-y'),
        y='count',
        tooltip=['rule','count']
    ).properties(width='container', height=300)
    st.altair_chart(chart, use_container_width=True)

def show_table_and_download(filtered):
    df = pd.DataFrame(filtered)
    if 'detail' in df.columns:
        df['detail'] = df['detail'].astype(str)

    st.subheader("⚠️ Alert Audit Trail")
    st.dataframe(df, height=400)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=df.columns)
    writer.writeheader()
    writer.writerows(df.to_dict(orient='records'))

    st.download_button(
        label="Download Alerts as CSV",
        data=buf.getvalue(),
        file_name="compliance_alerts.csv",
        mime="text/csv"
    )
