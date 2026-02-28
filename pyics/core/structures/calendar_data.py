#!/usr/bin/env python3
"""
pyics/core/structures/calendar_data.py
RFC 5545 VCALENDAR — Immutable Calendar Container

PROBLEM SOLVED: Fully RFC 5545-compliant frozen dataclass for VCALENDAR.
DEPENDENCIES: structures/data_types.py (CalScale),
              structures/immutable_event.py (ImmutableEvent),
              structures/timezone_data.py (ImmutableTimezone)
CONTRACT: Frozen dataclass. PRODID and VERSION are required. Events and
          timezones are stored as immutable tuples.

RFC 5545 §3.4 — iCalendar Object.

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — VCALENDAR Immutable Structure
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Optional, Tuple

from .data_types import CalScale
from .immutable_event import ImmutableEvent
from .timezone_data import ImmutableTimezone


# ---------------------------------------------------------------------------
# ImmutableCalendar — VCALENDAR object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImmutableCalendar:
    """
    RFC 5545 VCALENDAR object — fully immutable.

    Required by RFC 5545 (§3.4):
        PRODID  : product identifier (e.g. "-//OBINexus//Pyics//EN")
        VERSION : iCalendar version (always "2.0" for RFC 5545)

    Optional RFC 5545 properties:
        CALSCALE : calendar scale (default GREGORIAN)
        METHOD   : iTIP method (PUBLISH, REQUEST, REPLY, etc.)

    Sub-components:
        EVENTS    : tuple of ImmutableEvent (VEVENT) components
        TIMEZONES : tuple of ImmutableTimezone (VTIMEZONE) components

    Immutability guarantee:
        All fields are immutable. Use with_* methods to derive new
        instances — originals are never mutated.

    OBINexus default PRODID:  "-//OBINexus//Pyics 3.1//EN"
    """

    # --- Required ---
    prodid: str
    version: str = "2.0"

    # --- Optional calendar properties ---
    calscale: CalScale = CalScale.GREGORIAN
    method: Optional[str] = None     # PUBLISH | REQUEST | REPLY | ADD |
                                     # CANCEL | REFRESH | COUNTER |
                                     # DECLINECOUNTER

    # --- Sub-components ---
    events: Tuple[ImmutableEvent, ...] = ()
    timezones: Tuple[ImmutableTimezone, ...] = ()

    # -----------------------------------------------------------------------
    # Post-init validation
    # -----------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.prodid.strip():
            raise ValueError("PRODID must be a non-empty string (RFC 5545 §3.4)")
        if self.version != "2.0":
            raise ValueError(
                f"VERSION must be '2.0' for RFC 5545 compliance, got {self.version!r}"
            )
        if self.method is not None:
            _VALID_METHODS = {
                "PUBLISH", "REQUEST", "REPLY", "ADD",
                "CANCEL", "REFRESH", "COUNTER", "DECLINECOUNTER",
            }
            if self.method.upper() not in _VALID_METHODS:
                raise ValueError(
                    f"METHOD {self.method!r} is not a valid iTIP method. "
                    f"Valid: {sorted(_VALID_METHODS)}"
                )

    # -----------------------------------------------------------------------
    # Derived properties
    # -----------------------------------------------------------------------

    @property
    def event_count(self) -> int:
        """Number of VEVENT components."""
        return len(self.events)

    @property
    def timezone_count(self) -> int:
        """Number of VTIMEZONE components."""
        return len(self.timezones)

    @property
    def is_empty(self) -> bool:
        """True when the calendar contains no events."""
        return len(self.events) == 0

    def find_event(self, uid: str) -> Optional[ImmutableEvent]:
        """Return the first VEVENT with the given UID, or None."""
        for event in self.events:
            if event.uid == uid:
                return event
        return None

    def find_timezone(self, tzid: str) -> Optional[ImmutableTimezone]:
        """Return the VTIMEZONE with the given TZID, or None."""
        for tz in self.timezones:
            if tz.tzid == tzid:
                return tz
        return None

    # -----------------------------------------------------------------------
    # With-mutation helpers (pure — return new frozen instances)
    # -----------------------------------------------------------------------

    def with_event(self, event: ImmutableEvent) -> 'ImmutableCalendar':
        """Add a VEVENT component, returning a new calendar."""
        return replace(self, events=self.events + (event,))

    def with_timezone(self, tz: ImmutableTimezone) -> 'ImmutableCalendar':
        """Add a VTIMEZONE component, returning a new calendar."""
        return replace(self, timezones=self.timezones + (tz,))

    def replace_event(self, event: ImmutableEvent) -> 'ImmutableCalendar':
        """
        Replace an existing VEVENT by UID.

        If no event with the same UID exists, the new event is appended.
        """
        updated = tuple(
            event if e.uid == event.uid else e
            for e in self.events
        )
        if event.uid not in {e.uid for e in self.events}:
            updated = updated + (event,)
        return replace(self, events=updated)

    def remove_event(self, uid: str) -> 'ImmutableCalendar':
        """Remove a VEVENT by UID, returning a new calendar."""
        return replace(self, events=tuple(e for e in self.events if e.uid != uid))

    def with_method(self, method: str) -> 'ImmutableCalendar':
        return replace(self, method=method.upper())

    # -----------------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"ImmutableCalendar(prodid={self.prodid!r}, "
            f"events={self.event_count}, "
            f"timezones={self.timezone_count})"
        )


# ---------------------------------------------------------------------------
# Convenience constructor
# ---------------------------------------------------------------------------

def make_calendar(prodid: str = "-//OBINexus//Pyics 3.1//EN",
                  method: Optional[str] = None) -> ImmutableCalendar:
    """
    Construct an empty ImmutableCalendar with OBINexus default PRODID.

    Args:
        prodid : RFC 5545 PRODID string
        method : optional iTIP METHOD
    """
    return ImmutableCalendar(prodid=prodid, method=method)


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    'ImmutableCalendar',
    'make_calendar',
]

# [EOF] - End of structures/calendar_data.py
