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
    PEP_LIST_URL,
    OFAC_LIST_URL,
    PEP_LIST_LOCAL,
    OFAC_LIST_LOCAL,
    OWNERSHIP_GRAPH_LOCAL,
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
            amount = float(m.group('amount').replace(',', ''))
        except:
            amount = 0.0
        txs.append({
            "tx_id": m.group('tx_id'),
            "timestamp": m.group('timestamp'),
            "amount": amount
        })
    return txs

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_pep_list():
    try:
        resp = requests.get(PEP_LIST_URL, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
        if 'id' in df.columns:
            return set(df['id'].astype(str).dropna())
        if 'customer_id' in df.columns:
            return set(df['customer_id'].astype(str).dropna())
    except Exception:
        try:
            df = pd.read_csv(PEP_LIST_LOCAL)
            return set(df['customer_id'].astype(str).dropna())
        except Exception:
            st.warning("Could not load PEP list.")
            return set()

@st.cache_data(ttl=LIST_CACHE_TTL)
def load_ofac_list():
    try:
        resp = requests.get(OFAC_LIST_URL, timeout=10)
        resp.raise_for_status()
        df = pd.read_csv(io.StringIO(resp.text))
    except Exception:
        try:
            df = pd.read_csv(OFAC_LIST_LOCAL)
        except Exception:
            st.warning("Could not load OFAC list.")
            return set()
    ids = set()
    if 'account' in df.columns:
        ids |= set(df['account'].astype(str).dropna())
    if 'entity_name' in df.columns:
        ids |= set(df['entity_name'].astype(str).dropna())
    return ids

@st.cache_data
def load_ownership_graph(path=OWNERSHIP_GRAPH_LOCAL):
    graph = {}
    try:
        with open(path, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                parent, child = row['parent_id'], row['child_id']
                graph.setdefault(parent, []).append(child)
    except FileNotFoundError:
        return {}
    return graph