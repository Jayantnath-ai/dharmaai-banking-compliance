# config.py

from datetime import date

# Threshold defaults
CTR_THRESHOLD_DEFAULT             = 10_000
EXPOSURE_THRESHOLD_DEFAULT        = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT   = 5
MIN_RETENTION_YEARS_DEFAULT       = 5

# File extensions
STRUCTURED_EXT    = {'csv', 'json', 'xlsx'}
UNSTRUCTURED_EXT  = {'txt'}
ALL_EXTENSIONS    = STRUCTURED_EXT.union(UNSTRUCTURED_EXT)

# Default “From Date” filter
DATE_FILTER_DEFAULT = date(1970, 1, 1)

# Unstructured parsing regex
UNSTRUCTURED_PATTERN = (
    r"TXID[:=]\s*(?P<tx_id>\w+).*?"
    r"(Date|Timestamp)[:=]\s*(?P<timestamp>[\d\-T\:]+).*?"
    r"Amount[:=]\s*\$?(?P<amount>[\d,\.]+)"
)

# Bulk download URLs (CSV)
PEP_LIST_URL    = "https://www.opensanctions.org/datasets/peps/targets.simple.csv"    # :contentReference[oaicite:0]{index=0}
OFAC_LIST_URL   = "https://www.treasury.gov/ofac/downloads/sdn.csv"                   # 

# Local fallbacks (place your own test lists here)
PEP_LIST_LOCAL  = "data/pep_list.csv"
OFAC_LIST_LOCAL = "data/ofac_list.csv"

# Cache TTL (seconds)
LIST_CACHE_TTL  = 24 * 60 * 60
