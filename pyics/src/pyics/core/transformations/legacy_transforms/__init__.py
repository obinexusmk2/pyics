#!/usr/bin/env python3
"""
pyics/core/transforms/__init__.py
Transforms Domain Module

Engineering Lead: Nnamdi Okpala / OBINexus Computing
Domain: transforms
"""

# Import domain configuration
from .config import get_domain_metadata, validate_configuration, cost_metadata


def get_module_exports():
    """Export legacy transforms module contracts for domain registration."""
    return {
        'get_module_metadata': get_domain_metadata,
    }


# Export configuration interfaces
__all__ = [
    "get_domain_metadata",
    "validate_configuration",
    "cost_metadata",
    "get_module_exports",
]

# [EOF] - End of transforms domain module
