# data_loader.py

import pandas as pd
import requests
import io
import re
import streamlit as st

from config import (
    STRUCTURED_EXT,
    UNSTRUCTURED_EXT,
    UNSTRUCTURED_PATTERN,
    PEP_LIST_SOURCE,
    OFAC_LIST_SOURCE,
    LIST_CACHE_TTL
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

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_pep_list(source=PEP_LIST_SOURCE):
    """
    Fetch the PEP list via the OpenSanctions JSON API and return
    a set of entity IDs (customer_id).
    """
    if source.lower().startswith("http"):
        resp = requests.get(source)
        resp.raise_for_status()
        data = resp.json()
        results = data.get("results", [])
        return {
            ent.get("id")
            for ent in results
            if ent.get("schema") == "Person"
               and "peps" in ent.get("tags", [])
               and ent.get("id") is not None
        }
    else:
        df = pd.read_csv(source)
        return set(df['customer_id'].astype(str).dropna())

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_ofac_list(source=OFAC_LIST_SOURCE):
    """
    Fetch the OFAC SDN list (CSV) and return a set of account/entity identifiers.
    """
    if source.lower().startswith("http"):
        resp = requests.get(source)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    else:
        df = pd.read_csv(source)

    ids = set()
    if 'account' in df.columns:
        ids |= set(df['account'].astype(str).dropna())
    if 'entity_name' in df.columns:
        ids |= set(df['entity_name'].astype(str).dropna())
    return ids
