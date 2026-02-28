"""Domain configuration for validators."""

DOMAIN_CONFIG = {
    "domain_name": "validators",
    "version": "1.0.0",
    "enabled": True,
    "load_order": 50,
    "priority_index": 3,
    "compute_time_weight": 0.4,
    "exposure_type": "version_required",
}

cost_metadata = {
    "load_order": 50,
    "compute_time_weight": 0.4,
    "priority_index": 3,
}


def get_domain_metadata():
    return DOMAIN_CONFIG.copy()


def validate_configuration():
    required = {"domain_name", "version", "enabled"}
    return required.issubset(DOMAIN_CONFIG.keys())
