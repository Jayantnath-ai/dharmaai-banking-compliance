# data_loader.py - Encapsulates structured vs. unstructured loading
import pandas as pd
import re
from config import STRUCTURED_EXT, UNSTRUCTURED_EXT, UNSTRUCTURED_PATTERN

def load_structured(uploaded_file, ext):
    if ext == 'csv':
        df = pd.read_csv(uploaded_file)
    elif ext == 'json':
        df = pd.read_json(uploaded_file)
    else:  # 'xlsx'
        df = pd.read_excel(uploaded_file)
    return df.to_dict(orient='records')

def parse_unstructured(uploaded_file):
    """Parse only .txt uploads via regex extraction."""
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
            # other fields will default in engine if missing
        })
    return txs
