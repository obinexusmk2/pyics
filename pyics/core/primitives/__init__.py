"""Primitives domain - single-pass architecture."""
from .config import DOMAIN_CONFIG

def get_domain_metadata():
    return DOMAIN_CONFIG

__all__ = ["get_domain_metadata", "DOMAIN_CONFIG"]
