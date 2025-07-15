# data_loader.py

import pandas as pd
import re
import csv

from config import (
    STRUCTURED_EXT,
    UNSTRUCTURED_EXT,
    UNSTRUCTURED_PATTERN,
    PEP_LIST_SOURCE,
    OFAC_LIST_SOURCE
)

def load_structured(uploaded_file, ext):
    """
    Load structured transaction data from CSV, JSON, or Excel uploads.
    Returns a list of dicts.
    """
    if ext == 'csv':
        df = pd.read_csv(uploaded_file)
    elif ext == 'json':
        df = pd.read_json(uploaded_file)
    else:  # 'xlsx'
        df = pd.read_excel(uploaded_file)
    return df.to_dict(orient='records')


def parse_unstructured(uploaded_file):
    """
    Parse plain-text (.txt) uploads into transaction dicts using regex.
    Only supports extensions in UNSTRUCTURED_EXT.
    """
    name = uploaded_file.name.lower()
    if not any(name.endswith(f".{e}") for e in UNSTRUCTURED_EXT):
        return []

    # Read raw bytes and decode
    raw = uploaded_file.read()
    try:
        text = raw.decode('utf-8', errors='ignore')
    except:
        text = str(raw)

    # Extract TXID, timestamp, amount via regex
    pattern = re.compile(UNSTRUCTURED_PATTERN, re.IGNORECASE | re.DOTALL)
    txs = []
    for match in pattern.finditer(text):
        try:
            amount = float(match.group('amount').replace(',', ''))
        except:
            amount = 0.0
        txs.append({
            "tx_id":     match.group('tx_id'),
            "timestamp": match.group('timestamp'),
            "amount":    amount
            # Other fields (currency, customer_id, etc.) will be defaulted later
        })
    return txs


def load_pep_list(path=PEP_LIST_SOURCE):
    """
    Load Politically Exposed Persons (PEP) list from a CSV file.
    Expects a header 'customer_id'.
    Returns a set of customer_id strings.
    """
    peps = set()
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get('customer_id')
            if cid:
                peps.add(cid)
    return peps


def load_ofac_list(path=OFAC_LIST_SOURCE):
    """
    Load OFAC sanctions list from a CSV file.
    Expects a header 'account' or 'entity_name'.
    Returns a set of those identifiers.
    """
    ofac = set()
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            acct = row.get('account') or row.get('entity_name')
            if acct:
                ofac.add(acct)
    return ofac
