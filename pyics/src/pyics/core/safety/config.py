"""Domain configuration for safety."""

DOMAIN_CONFIG = {
    "domain_name": "safety",
    "version": "1.0.0",
    "enabled": True,
    "load_order": 90,
    "priority_index": 5,
    "compute_time_weight": 0.3,
    "exposure_type": "core_internal",
}

cost_metadata = {
    "load_order": 90,
    "compute_time_weight": 0.3,
    "priority_index": 5,
}


def get_domain_metadata():
    return DOMAIN_CONFIG.copy()


def validate_configuration():
    required = {"domain_name", "version", "enabled"}
    return required.issubset(DOMAIN_CONFIG.keys())
