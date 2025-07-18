from data_loader import (
    load_pep_list,
    load_ofac_list,
    load_ownership_graph
)
from rules import (
    evaluate_aml_rules,
    evaluate_pep_rule,
    evaluate_ofac_rule,
    evaluate_edd_hierarchy,
    evaluate_edd_sof,
    evaluate_sar_batch,
    evaluate_bcbs239_batch,
    evaluate_gdpr_rules,
    evaluate_sox_rules,
    evaluate_velocity_batch,
    evaluate_geo_jump_batch
)

def run_compliance(
    txs,
    ctr_threshold,
    exposure_threshold,
    sar_threshold,
    min_retention_years,
    enable_pep,
    enable_ofac,
    ownership_file,
    require_sof,
    sof_threshold,
    velocity_threshold,
    velocity_window_minutes,
    geojump_window_minutes
):
    pep_list  = load_pep_list() if enable_pep else set()
    ofac_list = load_ofac_list() if enable_ofac else set()

    # Load ownership graph (writes uploaded file if provided)
    graph = load_ownership_graph()

    alerts = []
    for tx in txs:
        alerts.extend(evaluate_aml_rules(tx, ctr_threshold))
        alerts.extend(evaluate_pep_rule(tx, pep_list, enable_pep))
        alerts.extend(evaluate_ofac_rule(tx, ofac_list, enable_ofac))
        alerts.extend(evaluate_edd_hierarchy(tx, graph))
        alerts.extend(evaluate_edd_sof(tx, require_sof, sof_threshold))

    alerts.extend(evaluate_velocity_batch(txs, velocity_threshold, velocity_window_minutes))
    alerts.extend(evaluate_geo_jump_batch(txs, geojump_window_minutes))
    alerts.extend(evaluate_sar_batch(txs, sar_threshold))
    alerts.extend(evaluate_bcbs239_batch(txs, exposure_threshold))

    for tx in txs:
        alerts.extend(evaluate_gdpr_rules(tx, min_retention_years))
        alerts.extend(evaluate_sox_rules(tx))

    return alerts
