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
    PEP_LIST_URL,
    OFAC_LIST_URL,
    PEP_LIST_LOCAL,
    OFAC_LIST_LOCAL,
    LIST_CACHE_TTL
)

def load_structured(uploaded_file, ext):
    if ext == 'csv':
        df = pd.read_csv(uploaded_file)
    elif ext == 'json':
        df = pd.read_json(uploaded_file)
    else:  # xlsx
        df = pd.read_excel(uploaded_file)
    return df.to_dict(orient='records')

def parse_unstructured(uploaded_file):
    name = uploaded_file.name.lower()
    if not any(name.endswith(f".{e}") for e in UNSTRUCTURED_EXT):
        return []
    raw = uploaded_file.read()
    try:
        text = raw.decode('utf-8', errors='ignore')
    except:
        text = str(raw)
    pattern = re.compile(UNSTRUCTURED_PATTERN, re.IGNORECASE | re.DOTALL)
    txs = []
    for m in pattern.finditer(text):
        try:
            amt = float(m.group('amount').replace(',', ''))
        except:
            amt = 0.0
        txs.append({
            "tx_id":     m.group('tx_id'),
            "timestamp": m.group('timestamp'),
            "amount":    amt
        })
    return txs

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_pep_list():
    """
    Attempt to download the bulk PEP CSV from OpenSanctions; if that fails,
    fall back to the local data/pep_list.csv.
    """
    try:
        resp = requests.get(PEP_LIST_URL, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        # 'targets.simple.csv' uses columns like 'id' and 'name'
        if 'id' in df.columns:
            return set(df['id'].astype(str).dropna())
        elif 'customer_id' in df.columns:
            return set(df['customer_id'].astype(str).dropna())
    except Exception:
        try:
            df = pd.read_csv(PEP_LIST_LOCAL)
            return set(df['customer_id'].astype(str).dropna())
        except Exception as e:
            st.warning(f"Could not load PEP list (download or local): {e}")
            return set()

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_ofac_list():
    """
    Download the OFAC SDN CSV; if that fails, fall back to data/ofac_list.csv.
    """
    try:
        resp = requests.get(OFAC_LIST_URL, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    except Exception:
        try:
            df = pd.read_csv(OFAC_LIST_LOCAL)
        except Exception as e:
            st.warning(f"Could not load OFAC list (download or local): {e}")
            return set()

    ids = set()
    if 'account' in df.columns:
        ids |= set(df['account'].astype(str).dropna())
    if 'entity_name' in df.columns:
        ids |= set(df['entity_name'].astype(str).dropna())
    return ids
