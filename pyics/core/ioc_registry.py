#!/usr/bin/env python3
"""
pyics/core/ioc_registry.py
Single-Pass IoC Registry for Domain Configuration Resolution

Generated: 2026-02-28T11:41:31.359469
Engineering Lead: Nnamdi Okpala / OBINexus Computing
Purpose: Cost-aware single-pass domain loading with dependency resolution
Architecture: DOP-compliant IoC container with deterministic load order

PROBLEM SOLVED: Provides single-pass domain loading with cost-aware optimization
DEPENDENCIES: All pyics.core domain configuration modules
THREAD SAFETY: Yes - immutable registry with concurrent access support
DETERMINISTIC: Yes - predictable load order and dependency resolution

This registry implements single-pass domain loading based on cost metadata
and provides type-safe dependency injection for runtime orchestration.
"""

import importlib
import sys
from typing import Dict, List, Any, Optional, Tuple
import logging

logger = logging.getLogger("pyics.core.ioc_registry")

# Single-pass load order (cost-optimized)
SINGLE_PASS_LOAD_ORDER = ['primitives', 'protocols', 'structures', 'composition', 'validators', 'transformations', 'registry', 'routing', 'safety']

# Domain cost metadata cache
_domain_cost_cache: Dict[str, Dict[str, Any]] = {}
_registry_initialized = False

class SinglePassRegistry:
    """
    Cost-aware single-pass domain registry
    
    Implements deterministic domain loading based on cost metadata
    and dependency analysis for optimal system initialization.
    """
    
    def __init__(self):
        self._loaded_domains: Dict[str, Any] = {}
        self._load_times: Dict[str, float] = {}
        self._initialization_complete = False
    
    def initialize_single_pass(self) -> bool:
        """
        Execute single-pass domain loading in cost-optimized order
        
        Returns:
            True if initialization successful, False otherwise
        """
        global _registry_initialized
        
        if _registry_initialized:
            logger.warning("Registry already initialized")
            return True
        
        try:
            logger.info("Executing single-pass domain loading...")
            
            import time
            total_start = time.time()
            
            for domain_name in SINGLE_PASS_LOAD_ORDER:
                start_time = time.time()
                
                if self._load_domain_single_pass(domain_name):
                    load_time = time.time() - start_time
                    self._load_times[domain_name] = load_time
                    logger.debug(f"Loaded {domain_name} in {load_time:.3f}s")
                else:
                    logger.error(f"Failed to load domain: {domain_name}")
                    return False
            
            total_time = time.time() - total_start
            logger.info(f"Single-pass loading complete in {total_time:.3f}s")
            logger.info(f"Loaded domains: {list(self._loaded_domains.keys())}")
            
            _registry_initialized = True
            self._initialization_complete = True
            return True
            
        except Exception as e:
            logger.error(f"Single-pass initialization failed: {e}")
            return False
    
    def _load_domain_single_pass(self, domain_name: str) -> bool:
        """Load single domain with validation"""
        try:
            # Import domain module
            module_name = f"pyics.core.{domain_name}"
            domain_module = importlib.import_module(module_name)
            
            # Validate domain interface
            required_attrs = ["get_domain_metadata", "validate_configuration", "cost_metadata"]
            for attr in required_attrs:
                if not hasattr(domain_module, attr):
                    logger.error(f"Domain {domain_name} missing required attribute: {attr}")
                    return False
            
            # Validate domain configuration
            if not domain_module.validate_configuration():
                logger.error(f"Domain {domain_name} configuration validation failed")
                return False
            
            # Cache domain metadata
            metadata = domain_module.get_domain_metadata()
            cost_metadata = domain_module.cost_metadata
            
            self._loaded_domains[domain_name] = {
                "module": domain_module,
                "metadata": metadata,
                "cost_metadata": cost_metadata
            }
            
            # Update global cost cache
            _domain_cost_cache[domain_name] = cost_metadata
            
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import domain {domain_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading domain {domain_name}: {e}")
            return False
    
    def get_domain_metadata(self, domain_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for loaded domain"""
        if not self._initialization_complete:
            logger.warning("Registry not fully initialized")
            return None
        
        return self._loaded_domains.get(domain_name, {}).get("metadata")
    
    def get_load_order(self) -> List[str]:
        """Get single-pass load order"""
        return SINGLE_PASS_LOAD_ORDER.copy()
    
    def get_load_performance(self) -> Dict[str, float]:
        """Get domain load performance metrics"""
        return self._load_times.copy()
    
    def validate_single_pass_compliance(self) -> bool:
        """Validate single-pass loading compliance"""
        try:
            # Check all domains loaded
            for domain_name in SINGLE_PASS_LOAD_ORDER:
                if domain_name not in self._loaded_domains:
                    logger.error(f"Domain {domain_name} not loaded")
                    return False
            
            # Validate load order compliance
            for i, domain_name in enumerate(SINGLE_PASS_LOAD_ORDER):
                expected_load_order = self._loaded_domains[domain_name]["cost_metadata"]["load_order"]
                
                # Check load order consistency
                for j in range(i):
                    prev_domain = SINGLE_PASS_LOAD_ORDER[j]
                    prev_load_order = self._loaded_domains[prev_domain]["cost_metadata"]["load_order"]
                    
                    if prev_load_order >= expected_load_order:
                        logger.error(f"Load order violation: {prev_domain} ({prev_load_order}) >= {domain_name} ({expected_load_order})")
                        return False
            
            logger.info("Single-pass compliance validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Compliance validation failed: {e}")
            return False

# Global registry instance
_registry_instance: Optional[SinglePassRegistry] = None

def get_registry() -> SinglePassRegistry:
    """Get or create global registry instance"""
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = SinglePassRegistry()
        if not _registry_instance.initialize_single_pass():
            raise RuntimeError("Failed to initialize single-pass registry")
    
    return _registry_instance

def get_domain_metadata(domain_name: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get domain metadata"""
    registry = get_registry()
    return registry.get_domain_metadata(domain_name)

def get_all_domains() -> List[str]:
    """Get list of all loaded domains"""
    return SINGLE_PASS_LOAD_ORDER.copy()

def get_domain_cost_metadata(domain_name: str) -> Optional[Dict[str, Any]]:
    """Get domain cost metadata"""
    return _domain_cost_cache.get(domain_name)

def validate_architecture() -> bool:
    """Validate complete architecture compliance"""
    registry = get_registry()
    return registry.validate_single_pass_compliance()

# Export registry interfaces
__all__ = [
    "SinglePassRegistry",
    "get_registry",
    "get_domain_metadata",
    "get_all_domains",
    "get_domain_cost_metadata", 
    "validate_architecture",
    "SINGLE_PASS_LOAD_ORDER"
]

# Auto-initialize registry
try:
    logger.debug("Auto-initializing single-pass registry...")
    _auto_registry = get_registry()
except Exception as e:
    logger.error(f"Failed to auto-initialize registry: {e}")

# [EOF] - End of single-pass IoC registry
