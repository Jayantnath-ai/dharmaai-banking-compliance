# config.py

from datetime import date

# Threshold defaults
CTR_THRESHOLD_DEFAULT             = 10_000
EXPOSURE_THRESHOLD_DEFAULT        = 100_000
SAR_TXN_COUNT_THRESHOLD_DEFAULT   = 5
MIN_RETENTION_YEARS_DEFAULT       = 5

# Supported file extensions
STRUCTURED_EXT     = {'csv', 'json', 'xlsx'}
UNSTRUCTURED_EXT   = {'txt'}
ALL_EXTENSIONS     = STRUCTURED_EXT.union(UNSTRUCTURED_EXT)

# Default “From Date” filter
DATE_FILTER_DEFAULT = date(1970, 1, 1)

# Regex pattern for parsing unstructured text
UNSTRUCTURED_PATTERN = (
    r"TXID[:=]\s*(?P<tx_id>\w+).*?"
    r"(Date|Timestamp)[:=]\s*(?P<timestamp>[\d\-T\:]+).*?"
    r"Amount[:=]\s*\$?(?P<amount>[\d,\.]+)"
)


# PEP list: query OpenSanctions JSON API for Politically Exposed Persons
PEP_LIST_SOURCE  = "https://api.opensanctions.org/entities.json?schema=Person&tag=peps&limit=10000"  # :contentReference[oaicite:0]{index=0}
# OFAC SDN list (CSV) from U.S. Treasury
OFAC_LIST_SOURCE = "https://home.treasury.gov/ofac/downloads/sdn.csv"                              # :contentReference[oaicite:1]{index=1}

# Cache TTL for remote list downloads (seconds) – 24 hours
LIST_CACHE_TTL    = 86400
