#!/usr/bin/env python3
"""
pyics/core/structures/immutable_event.py
RFC 5545 VEVENT — Immutable Calendar Event

PROBLEM SOLVED: Fully RFC 5545-compliant frozen dataclass for VEVENT.
DEPENDENCIES: structures/data_types.py, structures/alarm_data.py,
              structures/zkp_time.py
CONTRACT: Frozen dataclass. UID and DTSTART are required. DTEND and
          DURATION are mutually exclusive. Immutability is enforced by
          Python's frozen dataclass mechanism.

RFC 5545 §3.6.1 — VEVENT Component.

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — VEVENT Immutable Structure
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from typing import Optional, Tuple, Any

from .data_types import (
    EventStatus,
    ClassType,
    RecurrenceRule,
)
from .alarm_data import ImmutableAlarm
from .zkp_time import TridentTimeCapsule


# ---------------------------------------------------------------------------
# ImmutableEvent — VEVENT component
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImmutableEvent:
    """
    RFC 5545 VEVENT component — fully immutable.

    Required by RFC 5545 (§3.6.1):
        UID    : globally unique identifier
        DTSTART: start date-time of the event

    Optional RFC 5545 properties:
        DTEND        : end date-time (mutually exclusive with DURATION)
        DURATION     : duration of the event (mutually exclusive with DTEND)
        SUMMARY      : short text title
        DESCRIPTION  : longer descriptive text
        LOCATION     : location string
        ORGANIZER    : CAL-ADDRESS URI (e.g. "MAILTO:organizer@example.com")
        ATTENDEES    : tuple of CAL-ADDRESS URI strings
        STATUS       : EventStatus enum value
        CLASSIFICATION: ClassType enum value
        CREATED      : date-time of original creation
        LAST_MODIFIED: date-time of last modification
        SEQUENCE     : revision sequence number (default 0)
        RRULE        : RecurrenceRule for repeating events
        ALARMS       : tuple of ImmutableAlarm components

    ZKP extension:
        TIME_CAPSULE : optional TridentTimeCapsule for constraint scheduling

    Immutability guarantee:
        All fields are immutable. Use the with_* methods to derive new
        instances with modified fields — originals are never mutated.
    """

    # --- Required ---
    uid: str
    dtstart: datetime

    # --- Optional time properties ---
    dtend: Optional[datetime] = None
    duration: Optional[timedelta] = None

    # --- Text properties ---
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None

    # --- Participation ---
    organizer: Optional[str] = None           # MAILTO:... URI
    attendees: Tuple[str, ...] = ()           # tuple of MAILTO:... URIs

    # --- Status / classification ---
    status: EventStatus = EventStatus.CONFIRMED
    classification: ClassType = ClassType.PUBLIC

    # --- Audit fields ---
    created: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    sequence: int = 0

    # --- Recurrence ---
    rrule: Optional[RecurrenceRule] = None
    exdates: Tuple[datetime, ...] = ()        # EXDATE excluded occurrences

    # --- Sub-components ---
    alarms: Tuple[ImmutableAlarm, ...] = ()

    # --- ZKP extension ---
    time_capsule: Optional[TridentTimeCapsule] = None

    # -----------------------------------------------------------------------
    # Post-init validation (RFC 5545 §3.6.1 constraints)
    # -----------------------------------------------------------------------

    def __post_init__(self) -> None:
        if not self.uid.strip():
            raise ValueError("UID must be a non-empty string (RFC 5545 §3.6.1)")
        if self.dtend is not None and self.duration is not None:
            raise ValueError(
                "DTEND and DURATION are mutually exclusive in VEVENT "
                "(RFC 5545 §3.6.1)"
            )
        if self.dtend is not None and self.dtend <= self.dtstart:
            raise ValueError(
                f"DTEND ({self.dtend}) must be after DTSTART ({self.dtstart}) "
                "(RFC 5545 §3.6.1)"
            )
        if self.sequence < 0:
            raise ValueError(f"SEQUENCE must be non-negative, got {self.sequence}")

    # -----------------------------------------------------------------------
    # Derived properties
    # -----------------------------------------------------------------------

    @property
    def effective_end(self) -> Optional[datetime]:
        """
        The effective end date-time of the event.

        Returns DTEND if set; otherwise DTSTART + DURATION.
        Returns None if neither is set (instantaneous event).
        """
        if self.dtend is not None:
            return self.dtend
        if self.duration is not None:
            return self.dtstart + self.duration
        return None

    @property
    def effective_duration(self) -> Optional[timedelta]:
        """
        The effective duration of the event.

        Returns DURATION if set; otherwise DTEND - DTSTART.
        Returns None if neither DTEND nor DURATION is set.
        """
        if self.duration is not None:
            return self.duration
        if self.dtend is not None:
            return self.dtend - self.dtstart
        return None

    @property
    def is_recurring(self) -> bool:
        """True when the event has a recurrence rule."""
        return self.rrule is not None

    @property
    def has_alarms(self) -> bool:
        """True when the event has at least one VALARM component."""
        return len(self.alarms) > 0

    @property
    def has_time_capsule(self) -> bool:
        """True when a ZKP trident time capsule is attached."""
        return self.time_capsule is not None

    # -----------------------------------------------------------------------
    # With-mutation helpers (pure — return new frozen instances)
    # -----------------------------------------------------------------------

    def with_summary(self, summary: str) -> 'ImmutableEvent':
        return replace(self, summary=summary)

    def with_description(self, description: str) -> 'ImmutableEvent':
        return replace(self, description=description)

    def with_location(self, location: str) -> 'ImmutableEvent':
        return replace(self, location=location)

    def with_dtstart(self, dtstart: datetime) -> 'ImmutableEvent':
        return replace(self, dtstart=dtstart)

    def with_dtend(self, dtend: datetime) -> 'ImmutableEvent':
        if self.duration is not None:
            raise ValueError("Cannot set DTEND when DURATION is already set")
        return replace(self, dtend=dtend)

    def with_duration(self, duration: timedelta) -> 'ImmutableEvent':
        if self.dtend is not None:
            raise ValueError("Cannot set DURATION when DTEND is already set")
        return replace(self, duration=duration)

    def with_organizer(self, organizer: str) -> 'ImmutableEvent':
        return replace(self, organizer=organizer)

    def with_attendee(self, attendee: str) -> 'ImmutableEvent':
        return replace(self, attendees=self.attendees + (attendee,))

    def with_alarm(self, alarm: ImmutableAlarm) -> 'ImmutableEvent':
        return replace(self, alarms=self.alarms + (alarm,))

    def with_capsule(self, capsule: TridentTimeCapsule) -> 'ImmutableEvent':
        return replace(self, time_capsule=capsule)

    def with_rrule(self, rrule: RecurrenceRule) -> 'ImmutableEvent':
        return replace(self, rrule=rrule)

    def with_exdate(self, exdate: datetime) -> 'ImmutableEvent':
        return replace(self, exdates=self.exdates + (exdate,))

    def with_status(self, status: EventStatus) -> 'ImmutableEvent':
        return replace(self, status=status)

    def bump_sequence(self) -> 'ImmutableEvent':
        """Increment SEQUENCE by 1 (per RFC 5545 update protocol)."""
        return replace(self, sequence=self.sequence + 1)

    # -----------------------------------------------------------------------
    # Representation
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        end_str = ""
        if self.effective_end:
            end_str = f", end={self.effective_end.isoformat()}"
        summary_str = f", summary={self.summary!r}" if self.summary else ""
        return (
            f"ImmutableEvent(uid={self.uid!r}, "
            f"dtstart={self.dtstart.isoformat()}"
            f"{end_str}{summary_str})"
        )


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    'ImmutableEvent',
]

# [EOF] - End of structures/immutable_event.py
