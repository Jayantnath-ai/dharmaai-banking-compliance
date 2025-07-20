# agent.py

import logging
import json
from datetime import datetime
from pathlib import Path

from data_loader import load_structured, parse_unstructured
from generators import build_customer_map, gen_transaction
from engine import run_compliance
from config import (
    STRUCTURED_EXT,
    UNSTRUCTURED_EXT,
    CTR_THRESHOLD_DEFAULT,
    EXPOSURE_THRESHOLD_DEFAULT,
    SAR_TXN_COUNT_THRESHOLD_DEFAULT,
    MIN_RETENTION_YEARS_DEFAULT,
    REQUIRE_SOF_FOR_CASH,
    SOF_AMOUNT_THRESHOLD,
    VELOCITY_TXN_THRESHOLD_DEFAULT,
    VELOCITY_WINDOW_MINUTES_DEFAULT,
    GEOJUMP_WINDOW_MINUTES_DEFAULT
)

# Directories for incoming and processed files
INPUT_DIR = Path("data/incoming")
PROCESSED_DIR = Path("data/processed")

def fetch_latest_transactions():
    """
    Load all files from INPUT_DIR (structured or unstructured).
    Then move them to PROCESSED_DIR. If no files, generate mock data.
    """
    transactions = []
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    for file in INPUT_DIR.iterdir():
        ext = file.suffix.lstrip(".").lower()
        with file.open("rb") as f:
            if ext in STRUCTURED_EXT:
                transactions.extend(load_structured(f, ext))
            elif ext in UNSTRUCTURED_EXT:
                transactions.extend(parse_unstructured(f))
        # Move file after processing
        dest = PROCESSED_DIR / file.name
        file.replace(dest)

    if not transactions:
        # Fallback: mock data
        customer_map = build_customer_map()
        transactions = [gen_transaction(customer_map) for _ in range(200)]

    return transactions

def send_alerts(alerts):
    """
    Placeholder for your notification logic (Slack, email, etc.).
    For now, it prints to console.
    """
    for rule, entity, detail in alerts:
        print(f"[{datetime.utcnow().isoformat()}] ALERT: {rule} - {entity} - {detail}")

def adjust_thresholds(alerts):
    """
    Placeholder for threshold tuning logic based on false-positive rates.
    """
    logging.info(f"Adjust thresholds: received {len(alerts)} alerts (tuning not implemented)")

def log_run(transactions, alerts):
    """
    Append a JSON line to audit_log.jsonl with counts and details.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "tx_count": len(transactions),
        "alert_count": len(alerts),
        "alerts": alerts
    }
    with open("audit_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logging.info("=== DharmaAI Compliance Agent Run Started ===")

    # 1) Fetch or generate transactions
    txs = fetch_latest_transactions()
    logging.info(f"Loaded {len(txs)} transactions")

    # 2) Run compliance engine
    alerts = run_compliance(
        txs,
        ctr_threshold=CTR_THRESHOLD_DEFAULT,
        exposure_threshold=EXPOSURE_THRESHOLD_DEFAULT,
        sar_threshold=SAR_TXN_COUNT_THRESHOLD_DEFAULT,
        min_retention_years=MIN_RETENTION_YEARS_DEFAULT,
        enable_pep=True,
        enable_ofac=True,
        ownership_file=None,
        require_sof=REQUIRE_SOF_FOR_CASH,
        sof_threshold=SOF_AMOUNT_THRESHOLD,
        velocity_threshold=VELOCITY_TXN_THRESHOLD_DEFAULT,
        velocity_window_minutes=VELOCITY_WINDOW_MINUTES_DEFAULT,
        geojump_window_minutes=GEOJUMP_WINDOW_MINUTES_DEFAULT
    )
    logging.info(f"Compliance checks yielded {len(alerts)} alerts")

    # 3) Send notifications if any
    if alerts:
        send_alerts(alerts)

    # 4) Adjust thresholds based on alert outcomes
    adjust_thresholds(alerts)

    # 5) Log the run to audit
    log_run(txs, alerts)

    logging.info("=== DharmaAI Compliance Agent Run Completed ===")

if __name__ == "__main__":
    main()
