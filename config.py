# config.py

from datetime import date

# Threshold defaults
CTR_THRESHOLD_DEFAULT = 10_000
EXPOSURE_THRESHOLD_DEFAULT = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT = 5
MIN_RETENTION_YEARS_DEFAULT = 5

# Supported file extensions
STRUCTURED_EXT = {'csv', 'json', 'xlsx'}
UNSTRUCTURED_EXT = {'txt'}
ALL_EXTENSIONS = STRUCTURED_EXT.union(UNSTRUCTURED_EXT)

# Default “From Date” filter
DATE_FILTER_DEFAULT = date(1970, 1, 1)

# Regex pattern for parsing unstructured text
UNSTRUCTURED_PATTERN = (
    r"TXID[:=]\s*(?P<tx_id>\w+).*?"
    r"(Date|Timestamp)[:=]\s*(?P<timestamp>[\d\-T\:]+).*?"
    r"Amount[:=]\s*\$?(?P<amount>[\d,\.]+)"
)

# Dynamic PEP & OFAC list sources
PEP_LIST_SOURCE = "https://example.com/path/to/pep_list.csv"
OFAC_LIST_SOURCE = "https://home.treasury.gov/ofac/downloads/sdn.csv"

# Cache TTL for remote list downloads (seconds)
LIST_CACHE_TTL = 86400

