# engine.py

from rules import run_compliance_batch
from config import (
    CTR_THRESHOLD_DEFAULT,
    EXPOSURE_THRESHOLD_DEFAULT,
    SAR_TXN_COUNT_THRESHOLD_DEFAULT,
    MIN_RETENTION_YEARS_DEFAULT
)

def run_compliance(
    txs,
    ctr_threshold=CTR_THRESHOLD_DEFAULT,
    exposure_threshold=EXPOSURE_THRESHOLD_DEFAULT,
    sar_threshold=SAR_TXN_COUNT_THRESHOLD_DEFAULT,
    min_retention_years=MIN_RETENTION_YEARS_DEFAULT,
    enable_pep=True,
    enable_ofac=True
):
    """
    Wrapper around rules.run_compliance_batch that exposes toggles for PEP and OFAC screening.
    """
    return run_compliance_batch(
        txs,
        ctr_threshold=ctr_threshold,
        exposure_threshold=exposure_threshold,
        sar_threshold=sar_threshold,
        min_retention_years=min_retention_years,
        enable_pep=enable_pep,
        enable_ofac=enable_ofac
    )

