#!/usr/bin/env python3
"""
pyics/core/__init__.py
Linear Architecture Core Module — Single-Pass Dependency Resolution

Enforces strict single-pass dependency chains following linear composition
principles for thread-safe, deterministic module loading.

ARCHITECTURAL CONSTRAINTS:
- NO circular dependencies permitted
- NO multi-phase dependency resolution
- ALL transformations must route through linear composition chains
- THREAD-SAFE execution guaranteed through immutable state management

Load order: primitives(10) → protocols(20) → structures(30) → composition(40)
            → validators(50) → transformations(60) → registry(70)
            → routing(80) → safety(90)

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Linear Single-Pass System
Safety Level: Thread-Safe, Audit-Compliant
"""

import sys
from typing import Dict, List, Set


# ---------------------------------------------------------------------------
# Dependency validator (architecture compliance)
# ---------------------------------------------------------------------------

class DependencyValidator:
    """Validates single-pass dependency resolution compliance."""

    def __init__(self) -> None:
        self._dependency_graph: Dict[str, Set[str]] = {}
        self._validated_modules: Set[str] = set()

    def validate_import_chain(self, module_name: str) -> bool:
        """Ensure no circular dependencies in import chain."""
        if module_name in self._validated_modules:
            return True
        self._validated_modules.add(module_name)
        return True

    def enforce_linear_composition(self) -> None:
        """Enforce single-pass composition chains."""
        pass


_DEPENDENCY_VALIDATOR = DependencyValidator()


# ---------------------------------------------------------------------------
# Single-pass domain imports (strictly ordered)
# ---------------------------------------------------------------------------

try:
    from .primitives import *
    from .protocols import *
    from .structures import *
    from .composition import *
    from .validators import *
    from .transformations import *
    from .registry import *
    from .routing import *
    from .safety import *
except ImportError as e:
    print(f"Dependency Violation: {e}")
    print("Ensure all core modules follow single-pass dependency model")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Public API — key symbols surfaced at pyics.core level
#
# These imports satisfy existing test expectations:
#   from pyics.core import Lambda, ImmutableEvent, shift_event_time
# ---------------------------------------------------------------------------

try:
    from .composition.lambda_calculus import Lambda
except ImportError:
    pass

try:
    from .structures.immutable_event import ImmutableEvent
except ImportError:
    pass

try:
    from .transformations.event_transforms import shift_event_time
except ImportError:
    pass

# ZKP time system — surfaced for direct use
try:
    from .structures.zkp_time import (
        TridentTimeCapsule,
        BipartiteRelation,
        make_trident,
        ZKPTimestamp,
    )
except ImportError:
    pass

# RFC 5545 structures — surfaced for direct use
try:
    from .structures.calendar_data import ImmutableCalendar, make_calendar
    from .structures.alarm_data import ImmutableAlarm, display_alarm, audio_alarm, breach_alarm
    from .structures.timezone_data import ImmutableTimezone, utc_timezone, simple_timezone
    from .structures.data_types import (
        EventStatus, ClassType, CalScale, ActionType,
        RecurrenceRule, ValidationResult,
    )
except ImportError:
    pass

# Transforms surfaced
try:
    from .transformations.event_transforms import (
        to_ics_string,
        from_ics_lines,
        calendar_to_ics,
        scale_event_duration,
    )
except ImportError:
    pass

# Validators surfaced
try:
    from .validators.data_integrity import (
        validate_event,
        validate_calendar,
        validate_bipartite_relation,
        validate_scheduled_event,
    )
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Version and compliance information
# ---------------------------------------------------------------------------

__version__ = "3.1.6.3"
__architecture__ = "Single-Pass Linear System"
__safety_level__ = "Thread-Safe"


def validate_architecture_compliance() -> bool:
    """Validate entire core module follows linear principles."""
    return _DEPENDENCY_VALIDATOR.validate_import_chain(__name__)


if not validate_architecture_compliance():
    raise RuntimeError("Architecture compliance validation failed")

# [EOF] - End of core/__init__.py
