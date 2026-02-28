#!/usr/bin/env python3
"""
pyics/core/transformations/event_transforms.py
RFC 5545 iCalendar Serialization and Event Transforms

PROBLEM SOLVED: Pure functions for RFC 5545 ICS serialization/deserialization
                and immutable event transformations (shift, scale, etc.).
DEPENDENCIES: structures domain (ImmutableEvent, ImmutableCalendar, etc.)
CONTRACT: All functions are pure — no state mutation, no side effects.
          shift_event_time returns a Callable (higher-order transform).

RFC 5545 serialisation rules implemented:
  - Line folding: max 75 octets per line; continuation lines prefixed with SPACE
  - CRLF line endings (\\r\\n)
  - DTSTART/DTEND format: YYYYMMDDTHHMMSS (local) or YYYYMMDDTHHMMSSZ (UTC)
  - DURATION format: ±P[nW][nD][T[nH][nM][nS]]

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — RFC 5545 Transforms
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List, Optional, Tuple

from ..structures.data_types import (
    EventStatus,
    ClassType,
    ActionType,
    CalScale,
    RecurrenceRule,
    FreqType,
)
from ..structures.alarm_data import ImmutableAlarm
from ..structures.timezone_data import ImmutableTimezone, TimezoneComponent
from ..structures.immutable_event import ImmutableEvent
from ..structures.calendar_data import ImmutableCalendar


# ---------------------------------------------------------------------------
# RFC 5545 constants
# ---------------------------------------------------------------------------

_CRLF = "\r\n"
_FOLD_WIDTH = 75       # RFC 5545 §3.1 — content lines max 75 octets


# ---------------------------------------------------------------------------
# Pure time transform factories
# ---------------------------------------------------------------------------

def shift_event_time(delta: timedelta) -> Callable[[ImmutableEvent], ImmutableEvent]:
    """
    Returns a pure transform that shifts an event's DTSTART (and DTEND).

    The original event is never mutated. Alarms, UID, and all other
    properties are preserved verbatim.

    Usage:
        shift = shift_event_time(timedelta(hours=1))
        moved = shift(event)   # event unchanged; moved is a new instance
    """
    def _shift(event: ImmutableEvent) -> ImmutableEvent:
        new_dtstart = event.dtstart + delta
        new_dtend = (event.dtend + delta) if event.dtend is not None else None
        return replace(event, dtstart=new_dtstart, dtend=new_dtend)
    return _shift


def scale_event_duration(factor: float) -> Callable[[ImmutableEvent], ImmutableEvent]:
    """
    Returns a pure transform that scales the effective duration by *factor*.

    Works with both DTEND-based and DURATION-based events.
    """
    def _scale(event: ImmutableEvent) -> ImmutableEvent:
        if event.duration is not None:
            new_dur = timedelta(
                seconds=int(event.duration.total_seconds() * factor)
            )
            return replace(event, duration=new_dur)
        if event.dtend is not None:
            span = event.dtend - event.dtstart
            new_dtend = event.dtstart + timedelta(
                seconds=int(span.total_seconds() * factor)
            )
            return replace(event, dtend=new_dtend)
        return event  # no duration info — identity
    return _scale


# ---------------------------------------------------------------------------
# RFC 5545 serialisation helpers (pure functions)
# ---------------------------------------------------------------------------

def _fold_line(line: str) -> str:
    """
    Apply RFC 5545 §3.1 line folding.

    Lines longer than 75 characters are split with CRLF followed by a
    single space (linear whitespace).
    """
    if len(line) <= _FOLD_WIDTH:
        return line + _CRLF
    result = []
    while len(line) > _FOLD_WIDTH:
        result.append(line[:_FOLD_WIDTH])
        line = " " + line[_FOLD_WIDTH:]
    result.append(line)
    return _CRLF.join(result) + _CRLF


def _escape_text(text: str) -> str:
    """Apply RFC 5545 §3.3.11 TEXT escaping."""
    text = text.replace("\\", "\\\\")
    text = text.replace(";", "\\;")
    text = text.replace(",", "\\,")
    text = text.replace("\n", "\\n")
    return text


def _unescape_text(text: str) -> str:
    """Reverse RFC 5545 TEXT escaping."""
    text = text.replace("\\n", "\n")
    text = text.replace("\\,", ",")
    text = text.replace("\\;", ";")
    text = text.replace("\\\\", "\\")
    return text


def _format_datetime(dt: datetime) -> str:
    """Format a datetime to RFC 5545 DATE-TIME value."""
    if dt.tzinfo is not None and dt.utcoffset() == timedelta(0):
        return dt.strftime("%Y%m%dT%H%M%SZ")
    return dt.strftime("%Y%m%dT%H%M%S")


def _parse_datetime(value: str) -> datetime:
    """Parse RFC 5545 DATE-TIME value to datetime."""
    value = value.strip()
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(
            tzinfo=timezone.utc
        )
    if "T" in value:
        return datetime.strptime(value, "%Y%m%dT%H%M%S")
    return datetime.strptime(value, "%Y%m%d")


def _format_duration(delta: timedelta) -> str:
    """Format a timedelta to RFC 5545 DURATION value."""
    total_seconds = int(delta.total_seconds())
    sign = "-" if total_seconds < 0 else ""
    total_seconds = abs(total_seconds)

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    weeks, days = divmod(days, 7)

    result = f"{sign}P"
    if weeks:
        result += f"{weeks}W"
    if days:
        result += f"{days}D"
    if hours or minutes or seconds:
        result += "T"
        if hours:
            result += f"{hours}H"
        if minutes:
            result += f"{minutes}M"
        if seconds:
            result += f"{seconds}S"
    if result in ("P", "-P"):
        result += "T0S"
    return result


def _parse_duration(value: str) -> timedelta:
    """Parse RFC 5545 DURATION value to timedelta."""
    value = value.strip()
    sign = -1 if value.startswith("-") else 1
    value = value.lstrip("+-")
    if not value.startswith("P"):
        raise ValueError(f"Invalid DURATION value: {value!r}")
    value = value[1:]

    weeks = days = hours = minutes = seconds = 0
    m = re.match(r"(\d+)W", value)
    if m:
        weeks = int(m.group(1))
        value = value[m.end():]
    m = re.match(r"(\d+)D", value)
    if m:
        days = int(m.group(1))
        value = value[m.end():]
    if value.startswith("T"):
        value = value[1:]
        m = re.match(r"(\d+)H", value)
        if m:
            hours = int(m.group(1))
            value = value[m.end():]
        m = re.match(r"(\d+)M", value)
        if m:
            minutes = int(m.group(1))
            value = value[m.end():]
        m = re.match(r"(\d+)S", value)
        if m:
            seconds = int(m.group(1))

    delta = timedelta(weeks=weeks, days=days, hours=hours, minutes=minutes, seconds=seconds)
    return sign * delta


# ---------------------------------------------------------------------------
# VEVENT serialisation
# ---------------------------------------------------------------------------

def _alarm_to_ics(alarm: ImmutableAlarm) -> str:
    """Serialise an ImmutableAlarm to VALARM lines."""
    lines = ["BEGIN:VALARM"]
    lines.append(f"ACTION:{alarm.action.value}")
    lines.append(f"TRIGGER:{alarm.trigger_string()}")
    if alarm.description:
        lines.append(f"DESCRIPTION:{_escape_text(alarm.description)}")
    if alarm.duration is not None:
        lines.append(f"DURATION:{_format_duration(alarm.duration)}")
    if alarm.repeat:
        lines.append(f"REPEAT:{alarm.repeat}")
    lines.append("END:VALARM")
    return "".join(_fold_line(ln) for ln in lines)


def to_ics_string(event: ImmutableEvent) -> str:
    """
    Serialise an ImmutableEvent to a RFC 5545 VEVENT block.

    Returns a string with CRLF line endings, properly folded at 75 chars.
    """
    lines = ["BEGIN:VEVENT"]
    lines.append(f"UID:{event.uid}")
    lines.append(f"DTSTART:{_format_datetime(event.dtstart)}")

    if event.dtend is not None:
        lines.append(f"DTEND:{_format_datetime(event.dtend)}")
    elif event.duration is not None:
        lines.append(f"DURATION:{_format_duration(event.duration)}")

    if event.summary:
        lines.append(f"SUMMARY:{_escape_text(event.summary)}")
    if event.description:
        lines.append(f"DESCRIPTION:{_escape_text(event.description)}")
    if event.location:
        lines.append(f"LOCATION:{_escape_text(event.location)}")

    if event.organizer:
        lines.append(f"ORGANIZER:{event.organizer}")
    for attendee in event.attendees:
        lines.append(f"ATTENDEE:{attendee}")

    lines.append(f"STATUS:{event.status.value}")
    if event.classification != ClassType.PUBLIC:
        lines.append(f"CLASS:{event.classification.value}")

    if event.created is not None:
        lines.append(f"CREATED:{_format_datetime(event.created)}")
    if event.last_modified is not None:
        lines.append(f"LAST-MODIFIED:{_format_datetime(event.last_modified)}")
    lines.append(f"SEQUENCE:{event.sequence}")

    if event.rrule is not None:
        lines.append(f"RRULE:{event.rrule.to_rrule_string()}")
    for exdate in event.exdates:
        lines.append(f"EXDATE:{_format_datetime(exdate)}")

    body = "".join(_fold_line(ln) for ln in lines)
    for alarm in event.alarms:
        body += _alarm_to_ics(alarm)
    body += _fold_line("END:VEVENT")
    return body


# ---------------------------------------------------------------------------
# VTIMEZONE serialisation
# ---------------------------------------------------------------------------

def _tz_component_to_ics(component: TimezoneComponent, kind: str) -> str:
    lines = [f"BEGIN:{kind}"]
    lines.append(f"DTSTART:{_format_datetime(component.dtstart)}")
    lines.append(f"TZOFFSETFROM:{component.tzoffsetfrom}")
    lines.append(f"TZOFFSETTO:{component.tzoffsetto}")
    if component.tzname:
        lines.append(f"TZNAME:{component.tzname}")
    if component.rrule:
        lines.append(f"RRULE:{component.rrule.to_rrule_string()}")
    lines.append(f"END:{kind}")
    return "".join(_fold_line(ln) for ln in lines)


def timezone_to_ics(tz: ImmutableTimezone) -> str:
    """Serialise an ImmutableTimezone to a VTIMEZONE block."""
    body = _fold_line("BEGIN:VTIMEZONE")
    body += _fold_line(f"TZID:{tz.tzid}")
    if tz.standard:
        body += _tz_component_to_ics(tz.standard, "STANDARD")
    if tz.daylight:
        body += _tz_component_to_ics(tz.daylight, "DAYLIGHT")
    body += _fold_line("END:VTIMEZONE")
    return body


# ---------------------------------------------------------------------------
# VCALENDAR serialisation
# ---------------------------------------------------------------------------

def calendar_to_ics(calendar: ImmutableCalendar) -> str:
    """Serialise a full ImmutableCalendar to RFC 5545 .ics format."""
    lines = ["BEGIN:VCALENDAR"]
    lines.append(f"PRODID:{calendar.prodid}")
    lines.append(f"VERSION:{calendar.version}")
    lines.append(f"CALSCALE:{calendar.calscale.value}")
    if calendar.method:
        lines.append(f"METHOD:{calendar.method}")

    body = "".join(_fold_line(ln) for ln in lines)
    for tz in calendar.timezones:
        body += timezone_to_ics(tz)
    for event in calendar.events:
        body += to_ics_string(event)
    body += _fold_line("END:VCALENDAR")
    return body


# ---------------------------------------------------------------------------
# VEVENT parsing
# ---------------------------------------------------------------------------

def _unfold_lines(raw: str) -> List[str]:
    """Un-fold RFC 5545 content lines (join continuation lines)."""
    lines: List[str] = []
    for raw_line in raw.splitlines():
        if raw_line and raw_line[0] in (" ", "\t"):
            if lines:
                lines[-1] += raw_line[1:]
        else:
            lines.append(raw_line)
    return lines


def from_ics_lines(lines) -> ImmutableEvent:
    """
    Parse RFC 5545 VEVENT content lines into an ImmutableEvent.

    Accepts a list of strings or a single multi-line string.
    Continuation lines (starting with SPACE or TAB) are unfolded per RFC 5545 §3.1.
    """
    if isinstance(lines, list):
        lines = _unfold_lines("\n".join(lines))
    else:
        lines = _unfold_lines(lines)

    props: Dict[str, str] = {}
    alarms: List[ImmutableAlarm] = []
    in_alarm = False
    alarm_props: Dict[str, str] = {}

    for line in lines:
        line = line.rstrip("\r\n")
        if not line:
            continue
        if line == "BEGIN:VEVENT":
            continue
        if line == "END:VEVENT":
            break
        if line == "BEGIN:VALARM":
            in_alarm = True
            alarm_props = {}
            continue
        if line == "END:VALARM":
            in_alarm = False
            alarm = _parse_alarm(alarm_props)
            if alarm:
                alarms.append(alarm)
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key_name = key.split(";")[0].upper()
        if in_alarm:
            alarm_props[key_name] = value
        else:
            props[key_name] = value

    uid = props.get("UID", "")
    dtstart_str = props.get("DTSTART", "")
    if not uid or not dtstart_str:
        raise ValueError(
            "UID and DTSTART are required for VEVENT (RFC 5545 §3.6.1)"
        )

    dtstart = _parse_datetime(dtstart_str)
    dtend: Optional[datetime] = None
    duration: Optional[timedelta] = None
    if "DTEND" in props:
        dtend = _parse_datetime(props["DTEND"])
    elif "DURATION" in props:
        duration = _parse_duration(props["DURATION"])

    status = EventStatus.CONFIRMED
    if "STATUS" in props:
        try:
            status = EventStatus(props["STATUS"])
        except ValueError:
            pass

    classification = ClassType.PUBLIC
    if "CLASS" in props:
        try:
            classification = ClassType(props["CLASS"])
        except ValueError:
            pass

    created: Optional[datetime] = None
    if "CREATED" in props:
        created = _parse_datetime(props["CREATED"])

    last_modified: Optional[datetime] = None
    if "LAST-MODIFIED" in props:
        last_modified = _parse_datetime(props["LAST-MODIFIED"])

    sequence = 0
    if "SEQUENCE" in props:
        try:
            sequence = int(props["SEQUENCE"])
        except ValueError:
            pass

    rrule: Optional[RecurrenceRule] = None
    if "RRULE" in props:
        rrule = _parse_rrule(props["RRULE"])

    attendees: Tuple[str, ...] = ()
    if "ATTENDEE" in props:
        attendees = (props["ATTENDEE"],)

    exdates: Tuple[datetime, ...] = ()
    if "EXDATE" in props:
        exdates = tuple(_parse_datetime(v) for v in props["EXDATE"].split(","))

    return ImmutableEvent(
        uid=uid,
        dtstart=dtstart,
        dtend=dtend,
        duration=duration,
        summary=_unescape_text(props["SUMMARY"]) if "SUMMARY" in props else None,
        description=_unescape_text(props["DESCRIPTION"]) if "DESCRIPTION" in props else None,
        location=_unescape_text(props["LOCATION"]) if "LOCATION" in props else None,
        organizer=props.get("ORGANIZER"),
        attendees=attendees,
        status=status,
        classification=classification,
        created=created,
        last_modified=last_modified,
        sequence=sequence,
        rrule=rrule,
        exdates=exdates,
        alarms=tuple(alarms),
    )


def _parse_alarm(props: Dict[str, str]) -> Optional[ImmutableAlarm]:
    action_str = props.get("ACTION", "DISPLAY")
    try:
        action = ActionType(action_str)
    except ValueError:
        return None

    trigger_str = props.get("TRIGGER", "PT0S")
    trigger = _parse_duration(trigger_str)

    description = props.get("DESCRIPTION")
    if action == ActionType.DISPLAY and not description:
        description = "Reminder"

    duration: Optional[timedelta] = None
    if "DURATION" in props:
        duration = _parse_duration(props["DURATION"])

    repeat = 0
    if "REPEAT" in props:
        try:
            repeat = int(props["REPEAT"])
        except ValueError:
            pass

    return ImmutableAlarm(
        action=action,
        trigger=trigger,
        description=description,
        duration=duration,
        repeat=repeat,
    )


def _parse_rrule(value: str) -> RecurrenceRule:
    parts = {k: v for k, v in (p.split("=", 1) for p in value.split(";") if "=" in p)}
    freq_str = parts.get("FREQ", "DAILY")
    try:
        freq = FreqType(freq_str)
    except ValueError:
        freq = FreqType.DAILY

    count: Optional[int] = int(parts["COUNT"]) if "COUNT" in parts else None
    until: Optional[datetime] = _parse_datetime(parts["UNTIL"]) if "UNTIL" in parts else None
    interval = int(parts.get("INTERVAL", "1"))
    byday: Tuple[str, ...] = tuple(parts["BYDAY"].split(",")) if "BYDAY" in parts else ()
    bymonth: Tuple[int, ...] = tuple(int(m) for m in parts["BYMONTH"].split(",")) if "BYMONTH" in parts else ()
    bymonthday: Tuple[int, ...] = tuple(int(d) for d in parts["BYMONTHDAY"].split(",")) if "BYMONTHDAY" in parts else ()

    return RecurrenceRule(
        freq=freq, until=until, count=count, interval=interval,
        byday=byday, bymonth=bymonth, bymonthday=bymonthday,
    )


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------

__module_metadata__ = {
    "name": "event_transforms",
    "domain": "transformations",
    "problem_classification": "RFC 5545 iCalendar serialisation and pure transforms",
    "dependencies": ["structures"],
    "contracts": [],
    "thread_safe": True,
    "cost_weight": 0.3,
}


def get_module_exports() -> dict:
    return {
        'shift_event_time': shift_event_time,
        'scale_event_duration': scale_event_duration,
        'to_ics_string': to_ics_string,
        'from_ics_lines': from_ics_lines,
        'calendar_to_ics': calendar_to_ics,
        'timezone_to_ics': timezone_to_ics,
        'get_module_metadata': lambda: __module_metadata__.copy(),
    }


def initialize_module() -> bool:
    try:
        e = ImmutableEvent(uid="init-test", dtstart=datetime(2026, 1, 1, 9, 0))
        ics = to_ics_string(e)
        assert "BEGIN:VEVENT" in ics and "UID:init-test" in ics
        return True
    except Exception:
        return False


__all__ = [
    'shift_event_time',
    'scale_event_duration',
    'to_ics_string',
    'from_ics_lines',
    'calendar_to_ics',
    'timezone_to_ics',
    'get_module_exports',
    'initialize_module',
]

if not initialize_module():
    raise RuntimeError("Failed to initialize module: event_transforms.py")

# [EOF] - End of transformations/event_transforms.py
