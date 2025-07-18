import streamlit as st
from datetime import datetime
from config import (
    STRUCTURED_EXT,
    UNSTRUCTURED_EXT,
    DATE_FILTER_DEFAULT,
    CTR_THRESHOLD_DEFAULT,
    EXPOSURE_THRESHOLD_DEFAULT,
    SAR_TXN_COUNT_THRESHOLD_DEFAULT,
    MIN_RETENTION_YEARS_DEFAULT,
    VELOCITY_TXN_THRESHOLD_DEFAULT,
    VELOCITY_WINDOW_MINUTES_DEFAULT,
    GEOJUMP_WINDOW_MINUTES_DEFAULT
)
from data_loader import load_structured, parse_unstructured
from generators import build_customer_map, gen_transaction
from engine import run_compliance
from ui import (
    configure_page,
    sidebar_settings,
    show_metrics,
    show_chart,
    show_table_and_download
)
from rules import RULE_META

def main():
    configure_page()

    (
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
    ) = sidebar_settings(
        RULE_META,
        STRUCTURED_EXT,
        UNSTRUCTURED_EXT,
        DATE_FILTER_DEFAULT,
        CTR_THRESHOLD_DEFAULT,
        EXPOSURE_THRESHOLD_DEFAULT,
        SAR_TXN_COUNT_THRESHOLD_DEFAULT,
        MIN_RETENTION_YEARS_DEFAULT,
        VELOCITY_TXN_THRESHOLD_DEFAULT,
        VELOCITY_WINDOW_MINUTES_DEFAULT,
        GEOJUMP_WINDOW_MINUTES_DEFAULT
    )

    if st.button("Run Compliance Checks"):
        if uploaded_file:
            ext = uploaded_file.name.lower().split('.')[-1]
            if ext in STRUCTURED_EXT:
                txs = load_structured(uploaded_file, ext)
            else:
                txs = parse_unstructured(uploaded_file)
                if not txs:
                    st.error("No transactions parsed from unstructured file.")
                    return
        else:
            cust_map = build_customer_map()
            txs = [gen_transaction(cust_map) for _ in range(200)]

        raw_alerts = run_compliance(
            txs,
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
                except:
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

        filtered = [
            r for r in records
            if r["rule"] in selected_rules
            and r["regulation"] in selected_regs
            and r["date"] and r["date"] >= date_filter
        ]

        show_metrics(txs, filtered)
        show_chart(filtered)
        show_table_and_download(filtered)

if __name__ == "__main__":
    main()
