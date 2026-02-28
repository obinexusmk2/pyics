#!/usr/bin/env python3
"""
pyics/core/structures/timezone_data.py
RFC 5545 VTIMEZONE — Immutable Timezone Component

PROBLEM SOLVED: Immutable representation of VTIMEZONE (STANDARD + DAYLIGHT).
DEPENDENCIES: structures/data_types.py (RecurrenceRule)
CONTRACT: Frozen dataclass; TZID is RFC 5545 required.

RFC 5545 §3.6.5 — VTIMEZONE Component:
    Required: TZID
    Must contain: at least one STANDARD or DAYLIGHT sub-component

RFC 5545 §3.6.5 — STANDARD / DAYLIGHT sub-components:
    Required: DTSTART, TZOFFSETFROM, TZOFFSETTO

ZKP note: VTIMEZONE is treated as a *label* in ZKP mode — the actual
time calculation uses constraint offsets, not wall-clock timezone shifts.

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — VTIMEZONE Immutable Structure
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .data_types import RecurrenceRule


# ---------------------------------------------------------------------------
# TimezoneComponent — STANDARD or DAYLIGHT sub-component
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TimezoneComponent:
    """
    RFC 5545 STANDARD or DAYLIGHT sub-component of VTIMEZONE.

    Required by RFC 5545:
        DTSTART      : onset date-time of the component
        TZOFFSETFROM : UTC offset *before* this component takes effect
        TZOFFSETTO   : UTC offset *after* this component takes effect

    Optional:
        TZNAME : human-readable name (e.g. "GMT", "BST")
        RRULE  : recurrence rule for repeated transitions
    """
    dtstart: datetime
    tzoffsetfrom: str           # e.g. "+0000"  or "-0500"
    tzoffsetto: str             # e.g. "+0100"  or "-0400"
    tzname: Optional[str] = None
    rrule: Optional[RecurrenceRule] = None

    def __post_init__(self) -> None:
        _validate_utc_offset(self.tzoffsetfrom, "TZOFFSETFROM")
        _validate_utc_offset(self.tzoffsetto,   "TZOFFSETTO")

    def offset_delta_hours(self) -> float:
        """
        Net change in hours introduced by this transition.
        Positive → spring forward; negative → fall back.
        """
        return _parse_offset_hours(self.tzoffsetto) - _parse_offset_hours(self.tzoffsetfrom)

    def __repr__(self) -> str:
        name = f" ({self.tzname})" if self.tzname else ""
        return (
            f"TimezoneComponent({self.tzoffsetfrom}→{self.tzoffsetto}"
            f"{name}, from={self.dtstart.strftime('%Y-%m-%dT%H:%M')})"
        )


# ---------------------------------------------------------------------------
# ImmutableTimezone — VTIMEZONE component
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImmutableTimezone:
    """
    RFC 5545 VTIMEZONE component.

    Represents a timezone definition embedded in a VCALENDAR.
    Both *standard* and *daylight* are optional, but RFC 5545 requires at
    least one to be present for a valid VTIMEZONE.

    ZKP mode: in constraint-based scheduling, TZID acts as a *label* that
    identifies the timezone rule set without requiring wall-clock evaluation.

    Attributes:
        tzid     : timezone identifier (e.g. "Europe/London", "UTC")
        standard : STANDARD sub-component (winter / non-DST offset)
        daylight : DAYLIGHT sub-component (summer / DST offset)
    """
    tzid: str
    standard: Optional[TimezoneComponent] = None
    daylight: Optional[TimezoneComponent] = None

    def __post_init__(self) -> None:
        if not self.tzid.strip():
            raise ValueError("TZID must be a non-empty string (RFC 5545 §3.6.5)")
        if self.standard is None and self.daylight is None:
            raise ValueError(
                "VTIMEZONE must contain at least one STANDARD or DAYLIGHT "
                "sub-component (RFC 5545 §3.6.5)"
            )

    @property
    def has_dst(self) -> bool:
        """True when the timezone has a DST (DAYLIGHT) component."""
        return self.daylight is not None

    def with_standard(self, component: TimezoneComponent) -> 'ImmutableTimezone':
        return ImmutableTimezone(tzid=self.tzid, standard=component, daylight=self.daylight)

    def with_daylight(self, component: TimezoneComponent) -> 'ImmutableTimezone':
        return ImmutableTimezone(tzid=self.tzid, standard=self.standard, daylight=component)

    def __repr__(self) -> str:
        dst = " +DST" if self.has_dst else ""
        return f"ImmutableTimezone(tzid={self.tzid!r}{dst})"


# ---------------------------------------------------------------------------
# UTC offset helpers (pure functions)
# ---------------------------------------------------------------------------

def _validate_utc_offset(offset: str, field_name: str) -> None:
    """Validate an RFC 5545 UTC offset string (+HHMM or -HHMM)."""
    if not offset:
        raise ValueError(f"{field_name} must not be empty")
    if offset[0] not in ('+', '-'):
        raise ValueError(f"{field_name} must start with '+' or '-', got {offset!r}")
    digits = offset[1:]
    if len(digits) not in (4, 6) or not digits.isdigit():
        raise ValueError(
            f"{field_name} must be ±HHMM or ±HHMMSS, got {offset!r}"
        )


def _parse_offset_hours(offset: str) -> float:
    """Parse ±HHMM or ±HHMMSS offset string into fractional hours."""
    sign = 1 if offset[0] == '+' else -1
    digits = offset[1:]
    hours = int(digits[:2])
    minutes = int(digits[2:4])
    seconds = int(digits[4:6]) if len(digits) == 6 else 0
    return sign * (hours + minutes / 60.0 + seconds / 3600.0)


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def utc_timezone() -> ImmutableTimezone:
    """Return a minimal UTC VTIMEZONE component."""
    return ImmutableTimezone(
        tzid="UTC",
        standard=TimezoneComponent(
            dtstart=datetime(1970, 1, 1, 0, 0, 0),
            tzoffsetfrom="+0000",
            tzoffsetto="+0000",
            tzname="UTC",
        ),
    )


def simple_timezone(tzid: str, utc_offset: str, tzname: Optional[str] = None) -> ImmutableTimezone:
    """
    Construct a no-DST VTIMEZONE with a single STANDARD component.

    Args:
        tzid       : timezone identifier string
        utc_offset : UTC offset string in ±HHMM format (e.g. "+0100")
        tzname     : optional human-readable name
    """
    return ImmutableTimezone(
        tzid=tzid,
        standard=TimezoneComponent(
            dtstart=datetime(1970, 1, 1, 0, 0, 0),
            tzoffsetfrom=utc_offset,
            tzoffsetto=utc_offset,
            tzname=tzname,
        ),
    )


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    'TimezoneComponent',
    'ImmutableTimezone',
    'utc_timezone',
    'simple_timezone',
]

# [EOF] - End of structures/timezone_data.py
