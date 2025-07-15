# config.py - constants and defaults in one place
from datetime import date

# Threshold defaults
CTR_THRESHOLD_DEFAULT            = 10_000
EXPOSURE_THRESHOLD_DEFAULT       = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT  = 5
MIN_RETENTION_YEARS_DEFAULT      = 5

# Supported extensions
STRUCTURED_EXT      = {'csv', 'json', 'xlsx'}
UNSTRUCTURED_EXT    = {'txt'}
ALL_EXTENSIONS      = STRUCTURED_EXT.union(UNSTRUCTURED_EXT)

# Default “From Date” filter
DATE_FILTER_DEFAULT = date(1970, 1, 1)

# Regex for unstructured parsing
UNSTRUCTURED_PATTERN = (
    r"TXID[:=]\s*(?P<tx_id>\w+).*?"
    r"(Date|Timestamp)[:=]\s*(?P<timestamp>[\d\-T\:]+).*?"
    r"Amount[:=]\s*\$?(?P<amount>[\d,\.]+)"
)


# PEP & OFAC sources (can be local path or HTTP URL)
PEP_LIST_SOURCE   = "data/pep_list.csv"
OFAC_LIST_SOURCE  = "data/ofac_list.csv"
