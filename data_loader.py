# data_loader.py

import pandas as pd
import requests
import io
import re
import csv
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
    if ext == 'csv':
        df = pd.read_csv(uploaded_file)
    elif ext == 'json':
        df = pd.read_json(uploaded_file)
    else:  # 'xlsx'
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
            amount = float(m.group('amount').replace(',', ''))
        except:
            amount = 0.0
        txs.append({
            "tx_id":     m.group('tx_id'),
            "timestamp": m.group('timestamp'),
            "amount":    amount
        })
    return txs

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_pep_list(source=PEP_LIST_SOURCE):
    # Fetch or read PEP list, returning a set of customer_id strings.
    # Cached for LIST_CACHE_TTL seconds.
 
    if source.lower().startswith("http"):
        resp = requests.get(source)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    else:
        df = pd.read_csv(source)
    return set(df['customer_id'].astype(str).dropna())

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_ofac_list(source=OFAC_LIST_SOURCE):
    #"""Fetch or read OFAC list, returning a set of account/entity identifiers.Cached for LIST_CACHE_TTL seconds."""
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
