"""Domain configuration for composition."""

DOMAIN_CONFIG = {
    "domain_name": "composition",
    "version": "1.0.0",
    "enabled": True,
    "load_order": 40,
    "priority_index": 2,
    "compute_time_weight": 0.3,
    "exposure_type": "version_required",
}

cost_metadata = {
    "load_order": 40,
    "compute_time_weight": 0.3,
    "priority_index": 2,
}


def get_domain_metadata():
    return DOMAIN_CONFIG.copy()


def validate_configuration():
    required = {"domain_name", "version", "enabled"}
    return required.issubset(DOMAIN_CONFIG.keys())
