"""
pyics/core/structures/__init__.py
Structures Domain — RFC 5545 Immutable Calendar Components

Single-pass load order: 30
Dependency level: 2 (depends on primitives, protocols)

Exports all RFC 5545 structural types and the ZKP time system.
"""

from .config import DOMAIN_CONFIG

# RFC 5545 data types and enumerations
from .data_types import (
    ParticipationStatus,
    EventStatus,
    TodoStatus,
    CalUserType,
    CalScale,
    ClassType,
    FreqType,
    WeekdayType,
    ActionType,
    RoleType,
    RecurrenceRule,
    ValidationResult,
)

# ZKP time system (Trident + Bipartite discriminant)
from .zkp_time import (
    ZKPTimestamp,
    TridentTimeCapsule,
    BipartiteRelation,
    make_trident,
)

# RFC 5545 components
from .alarm_data import (
    ImmutableAlarm,
    display_alarm,
    audio_alarm,
    breach_alarm,
)

from .timezone_data import (
    TimezoneComponent,
    ImmutableTimezone,
    utc_timezone,
    simple_timezone,
)

from .immutable_event import ImmutableEvent

from .calendar_data import (
    ImmutableCalendar,
    make_calendar,
)


def get_domain_metadata() -> dict:
    return DOMAIN_CONFIG


__all__ = [
    # Domain metadata
    "get_domain_metadata",
    "DOMAIN_CONFIG",
    # Data types / enumerations
    "ParticipationStatus",
    "EventStatus",
    "TodoStatus",
    "CalUserType",
    "CalScale",
    "ClassType",
    "FreqType",
    "WeekdayType",
    "ActionType",
    "RoleType",
    "RecurrenceRule",
    "ValidationResult",
    # ZKP time system
    "ZKPTimestamp",
    "TridentTimeCapsule",
    "BipartiteRelation",
    "make_trident",
    # VALARM
    "ImmutableAlarm",
    "display_alarm",
    "audio_alarm",
    "breach_alarm",
    # VTIMEZONE
    "TimezoneComponent",
    "ImmutableTimezone",
    "utc_timezone",
    "simple_timezone",
    # VEVENT
    "ImmutableEvent",
    # VCALENDAR
    "ImmutableCalendar",
    "make_calendar",
]
