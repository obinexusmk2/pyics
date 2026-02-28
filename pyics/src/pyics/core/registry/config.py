"""Domain configuration for registry."""

DOMAIN_CONFIG = {
    "domain_name": "registry",
    "version": "1.0.0",
    "enabled": True,
    "load_order": 70,
    "priority_index": 4,
    "compute_time_weight": 0.5,
    "exposure_type": "version_required",
}

cost_metadata = {
    "load_order": 70,
    "compute_time_weight": 0.5,
    "priority_index": 4,
}


def get_domain_metadata():
    return DOMAIN_CONFIG.copy()


def validate_configuration():
    required = {"domain_name", "version", "enabled"}
    return required.issubset(DOMAIN_CONFIG.keys())
