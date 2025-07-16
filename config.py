# config.py

from datetime import date

# Threshold defaults
CTR_THRESHOLD_DEFAULT            = 10_000
EXPOSURE_THRESHOLD_DEFAULT       = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT  = 5
MIN_RETENTION_YEARS_DEFAULT      = 5

# Supported file extensions
STRUCTURED_EXT    = {'csv', 'json', 'xlsx'}
UNSTRUCTURED_EXT  = {'txt'}
ALL_EXTENSIONS    = STRUCTURED_EXT.union(UNSTRUCTURED_EXT)

# Default “From Date” filter
DATE_FILTER_DEFAULT = date(1970, 1, 1)

# Regex pattern for parsing unstructured text
UNSTRUCTURED_PATTERN = (
    r"TXID[:=]\s*(?P<tx_id>\w+).*?"
    r"(Date|Timestamp)[:=]\s*(?P<timestamp>[\d\-T\:]+).*?"
    r"Amount[:=]\s*\$?(?P<amount>[\d,\.]+)"
)

# Bulk download URLs (CSV)
PEP_LIST_URL    = "https://www.opensanctions.org/datasets/peps/targets.simple.csv"
OFAC_LIST_URL   = "https://www.treasury.gov/ofac/downloads/sdn.csv"

# Local fallbacks
PEP_LIST_LOCAL  = "data/pep_list.csv"
OFAC_LIST_LOCAL = "data/ofac_list.csv"
OWNERSHIP_GRAPH_LOCAL = "data/ownership_graph.csv"

# Cache TTL for list downloads (seconds)
LIST_CACHE_TTL = 24 * 60 * 60

# EDD defaults
REQUIRE_SOF_FOR_CASH = True
SOF_AMOUNT_THRESHOLD = 10000