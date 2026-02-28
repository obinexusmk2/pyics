#!/usr/bin/env python3
"""
pyics/core/structures/data_types.py
RFC 5545 iCalendar Data Type Definitions

PROBLEM SOLVED: RFC 5545-compliant enumerations and value types for all
                calendar components (VEVENT, VTIMEZONE, VALARM, VCALENDAR).
DEPENDENCIES: Standard library only (enum, dataclasses, datetime)
CONTRACT: Immutable enumerations and frozen dataclasses; no mutable state.

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — RFC 5545 Foundation Types
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta, date


# ---------------------------------------------------------------------------
# RFC 5545 §3.2.12 — Participation Status
# ---------------------------------------------------------------------------

class ParticipationStatus(Enum):
    """PARTSTAT parameter values (RFC 5545 §3.2.12)."""
    NEEDS_ACTION = "NEEDS-ACTION"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    TENTATIVE = "TENTATIVE"
    DELEGATED = "DELEGATED"


# ---------------------------------------------------------------------------
# RFC 5545 §3.3.9 — STATUS property for VEVENT
# ---------------------------------------------------------------------------

class EventStatus(Enum):
    """STATUS property values for VEVENT (RFC 5545 §3.8.1.11)."""
    TENTATIVE = "TENTATIVE"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class TodoStatus(Enum):
    """STATUS property values for VTODO (RFC 5545 §3.8.1.11)."""
    NEEDS_ACTION = "NEEDS-ACTION"
    COMPLETED = "COMPLETED"
    IN_PROCESS = "IN-PROCESS"
    CANCELLED = "CANCELLED"


# ---------------------------------------------------------------------------
# RFC 5545 §3.2.3 — Calendar User Type
# ---------------------------------------------------------------------------

class CalUserType(Enum):
    """CUTYPE parameter values (RFC 5545 §3.2.3)."""
    INDIVIDUAL = "INDIVIDUAL"
    GROUP = "GROUP"
    RESOURCE = "RESOURCE"
    ROOM = "ROOM"
    UNKNOWN = "UNKNOWN"


# ---------------------------------------------------------------------------
# RFC 5545 §3.7.1 — CALSCALE
# ---------------------------------------------------------------------------

class CalScale(Enum):
    """CALSCALE property values (RFC 5545 §3.7.1)."""
    GREGORIAN = "GREGORIAN"


# ---------------------------------------------------------------------------
# RFC 5545 §3.8.1.3 — CLASS
# ---------------------------------------------------------------------------

class ClassType(Enum):
    """CLASS property values (RFC 5545 §3.8.1.3)."""
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    CONFIDENTIAL = "CONFIDENTIAL"


# ---------------------------------------------------------------------------
# RFC 5545 §3.3.10 — RRULE frequency
# ---------------------------------------------------------------------------

class FreqType(Enum):
    """FREQ values for RECUR value type (RFC 5545 §3.3.10)."""
    SECONDLY = "SECONDLY"
    MINUTELY = "MINUTELY"
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class WeekdayType(Enum):
    """Weekday abbreviations for BYDAY rule part (RFC 5545 §3.3.10)."""
    MO = "MO"
    TU = "TU"
    WE = "WE"
    TH = "TH"
    FR = "FR"
    SA = "SA"
    SU = "SU"


# ---------------------------------------------------------------------------
# RFC 5545 §3.8.6.1 — ACTION for VALARM
# ---------------------------------------------------------------------------

class ActionType(Enum):
    """ACTION property values for VALARM (RFC 5545 §3.8.6.1)."""
    AUDIO = "AUDIO"
    DISPLAY = "DISPLAY"
    EMAIL = "EMAIL"


# ---------------------------------------------------------------------------
# RFC 5545 §3.2.16 — ROLE
# ---------------------------------------------------------------------------

class RoleType(Enum):
    """ROLE parameter values (RFC 5545 §3.2.16)."""
    CHAIR = "CHAIR"
    REQ_PARTICIPANT = "REQ-PARTICIPANT"
    OPT_PARTICIPANT = "OPT-PARTICIPANT"
    NON_PARTICIPANT = "NON-PARTICIPANT"


# ---------------------------------------------------------------------------
# RFC 5545 §3.3.10 — RecurrenceRule (RRULE value)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RecurrenceRule:
    """
    RRULE value type (RFC 5545 §3.3.10).

    Represents a recurrence rule for repeating calendar components.
    All fields are optional except freq.
    """
    freq: FreqType
    until: Optional[datetime] = None          # UNTIL — end of recurrence
    count: Optional[int] = None               # COUNT — number of occurrences
    interval: int = 1                         # INTERVAL (default 1)
    bysecond: Tuple[int, ...] = ()            # BYSECOND
    byminute: Tuple[int, ...] = ()            # BYMINUTE
    byhour: Tuple[int, ...] = ()              # BYHOUR
    byday: Tuple[str, ...] = ()               # BYDAY e.g. ("MO", "FR", "2TU")
    bymonthday: Tuple[int, ...] = ()          # BYMONTHDAY
    byyearday: Tuple[int, ...] = ()           # BYYEARDAY
    byweekno: Tuple[int, ...] = ()            # BYWEEKNO
    bymonth: Tuple[int, ...] = ()             # BYMONTH
    bysetpos: Tuple[int, ...] = ()            # BYSETPOS
    wkst: WeekdayType = WeekdayType.MO        # WKST (week start, default MO)

    def to_rrule_string(self) -> str:
        """Serialize to RFC 5545 RRULE value string."""
        parts = [f"FREQ={self.freq.value}"]
        if self.until is not None:
            parts.append(f"UNTIL={self.until.strftime('%Y%m%dT%H%M%SZ')}")
        if self.count is not None:
            parts.append(f"COUNT={self.count}")
        if self.interval != 1:
            parts.append(f"INTERVAL={self.interval}")
        if self.bysecond:
            parts.append(f"BYSECOND={','.join(str(s) for s in self.bysecond)}")
        if self.byminute:
            parts.append(f"BYMINUTE={','.join(str(m) for m in self.byminute)}")
        if self.byhour:
            parts.append(f"BYHOUR={','.join(str(h) for h in self.byhour)}")
        if self.byday:
            parts.append(f"BYDAY={','.join(self.byday)}")
        if self.bymonthday:
            parts.append(f"BYMONTHDAY={','.join(str(d) for d in self.bymonthday)}")
        if self.byyearday:
            parts.append(f"BYYEARDAY={','.join(str(d) for d in self.byyearday)}")
        if self.byweekno:
            parts.append(f"BYWEEKNO={','.join(str(w) for w in self.byweekno)}")
        if self.bymonth:
            parts.append(f"BYMONTH={','.join(str(m) for m in self.bymonth)}")
        if self.bysetpos:
            parts.append(f"BYSETPOS={','.join(str(p) for p in self.bysetpos)}")
        if self.wkst != WeekdayType.MO:
            parts.append(f"WKST={self.wkst.value}")
        return ";".join(parts)


# ---------------------------------------------------------------------------
# ValidationResult — shared by validators domain
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ValidationResult:
    """Immutable result from a validation operation."""
    valid: bool
    errors: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0

    def with_error(self, msg: str) -> 'ValidationResult':
        return ValidationResult(
            valid=False,
            errors=self.errors + (msg,),
            warnings=self.warnings,
        )

    def with_warning(self, msg: str) -> 'ValidationResult':
        return ValidationResult(
            valid=self.valid,
            errors=self.errors,
            warnings=self.warnings + (msg,),
        )

    @classmethod
    def ok(cls) -> 'ValidationResult':
        return cls(valid=True)

    @classmethod
    def fail(cls, *errors: str) -> 'ValidationResult':
        return cls(valid=False, errors=tuple(errors))


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    # Enumerations
    'ParticipationStatus',
    'EventStatus',
    'TodoStatus',
    'CalUserType',
    'CalScale',
    'ClassType',
    'FreqType',
    'WeekdayType',
    'ActionType',
    'RoleType',
    # Value types
    'RecurrenceRule',
    'ValidationResult',
]

# [EOF] - End of structures/data_types.py
