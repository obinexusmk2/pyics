#!/usr/bin/env python3
"""
pyics/core/validators/data_integrity.py
RFC 5545 iCalendar Data Integrity Validators

PROBLEM SOLVED: Pure validation functions for RFC 5545 required-property
                constraints and discriminant-based bipartite breach detection.
DEPENDENCIES: structures domain (ImmutableEvent, ImmutableCalendar,
              BipartiteRelation, ValidationResult)
CONTRACT: All functions are pure — no mutation, no side effects.
          All return ValidationResult (frozen dataclass).

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — RFC 5545 Validation + Discriminant Checks
"""

from __future__ import annotations

from typing import Any, Dict

from ..structures.data_types import ValidationResult
from ..structures.immutable_event import ImmutableEvent
from ..structures.calendar_data import ImmutableCalendar
from ..structures.alarm_data import ImmutableAlarm
from ..structures.timezone_data import ImmutableTimezone
from ..structures.zkp_time import BipartiteRelation, TridentTimeCapsule


# ---------------------------------------------------------------------------
# RFC 5545 §3.6.1 — VEVENT validation
# ---------------------------------------------------------------------------

def validate_event(event: ImmutableEvent) -> ValidationResult:
    """
    Validate an ImmutableEvent against RFC 5545 §3.6.1 constraints.

    Required properties:
        UID    — must be non-empty
        DTSTART— must be present

    Mutual exclusions:
        DTEND and DURATION must not both be set

    Sequence:
        SEQUENCE must be >= 0

    Returns ValidationResult with any violations accumulated.
    """
    result = ValidationResult.ok()

    # UID required (RFC 5545 §3.8.4.7)
    if not event.uid.strip():
        result = result.with_error("UID must be a non-empty string (RFC 5545 §3.8.4.7)")

    # DTSTART required (RFC 5545 §3.8.2.4)
    if event.dtstart is None:
        result = result.with_error("DTSTART is required for VEVENT (RFC 5545 §3.8.2.4)")

    # DTEND / DURATION mutual exclusion (RFC 5545 §3.6.1)
    if event.dtend is not None and event.duration is not None:
        result = result.with_error(
            "DTEND and DURATION are mutually exclusive (RFC 5545 §3.6.1)"
        )

    # DTEND must be after DTSTART (RFC 5545 §3.6.1)
    if event.dtend is not None and event.dtstart is not None:
        if event.dtend <= event.dtstart:
            result = result.with_error(
                f"DTEND ({event.dtend.isoformat()}) must be strictly after "
                f"DTSTART ({event.dtstart.isoformat()}) (RFC 5545 §3.6.1)"
            )

    # SEQUENCE non-negative
    if event.sequence < 0:
        result = result.with_error(
            f"SEQUENCE must be non-negative, got {event.sequence}"
        )

    # Warn about missing SUMMARY (not required, but common courtesy)
    if not event.summary:
        result = result.with_warning(
            "SUMMARY is missing; recommended for calendar interoperability"
        )

    # Validate each VALARM sub-component
    for i, alarm in enumerate(event.alarms):
        alarm_result = validate_alarm(alarm)
        for err in alarm_result.errors:
            result = result.with_error(f"VALARM[{i}]: {err}")
        for warn in alarm_result.warnings:
            result = result.with_warning(f"VALARM[{i}]: {warn}")

    return result


# ---------------------------------------------------------------------------
# RFC 5545 §3.6.6 — VALARM validation
# ---------------------------------------------------------------------------

def validate_alarm(alarm: ImmutableAlarm) -> ValidationResult:
    """
    Validate an ImmutableAlarm against RFC 5545 §3.6.6 constraints.

    Required: ACTION, TRIGGER (always set by ImmutableAlarm constructor)
    DISPLAY alarms must have DESCRIPTION.
    REPEAT requires DURATION.
    """
    result = ValidationResult.ok()

    if alarm.repeat > 0 and alarm.duration is None:
        result = result.with_error(
            "DURATION is required when REPEAT > 0 (RFC 5545 §3.6.6)"
        )

    from ..structures.data_types import ActionType
    if alarm.action == ActionType.DISPLAY and not alarm.description:
        result = result.with_error(
            "DESCRIPTION is required for DISPLAY alarms (RFC 5545 §3.6.6)"
        )

    return result


# ---------------------------------------------------------------------------
# RFC 5545 §3.4 — VCALENDAR validation
# ---------------------------------------------------------------------------

def validate_calendar(calendar: ImmutableCalendar) -> ValidationResult:
    """
    Validate an ImmutableCalendar against RFC 5545 §3.4 constraints.

    Required: PRODID, VERSION
    VERSION must be "2.0" for RFC 5545 compliance.
    Each VEVENT is validated recursively.
    """
    result = ValidationResult.ok()

    if not calendar.prodid.strip():
        result = result.with_error("PRODID must be non-empty (RFC 5545 §3.4)")

    if calendar.version != "2.0":
        result = result.with_error(
            f"VERSION must be '2.0', got {calendar.version!r} (RFC 5545 §3.4)"
        )

    # Validate each VEVENT
    for i, event in enumerate(calendar.events):
        event_result = validate_event(event)
        for err in event_result.errors:
            result = result.with_error(f"VEVENT[{i}] (uid={event.uid!r}): {err}")
        for warn in event_result.warnings:
            result = result.with_warning(f"VEVENT[{i}] (uid={event.uid!r}): {warn}")

    # Warn if no events at all
    if calendar.event_count == 0:
        result = result.with_warning("Calendar contains no VEVENT components")

    # Check for duplicate UIDs
    seen_uids: set = set()
    for event in calendar.events:
        if event.uid in seen_uids:
            result = result.with_error(
                f"Duplicate UID detected: {event.uid!r} "
                "(RFC 5545 §3.8.4.7 — UID must be globally unique)"
            )
        seen_uids.add(event.uid)

    return result


# ---------------------------------------------------------------------------
# RFC 5545 §3.6.5 — VTIMEZONE validation
# ---------------------------------------------------------------------------

def validate_timezone(tz: ImmutableTimezone) -> ValidationResult:
    """
    Validate an ImmutableTimezone against RFC 5545 §3.6.5 constraints.

    Required: TZID
    Must have at least one STANDARD or DAYLIGHT sub-component.
    """
    result = ValidationResult.ok()

    if not tz.tzid.strip():
        result = result.with_error("TZID must be non-empty (RFC 5545 §3.6.5)")

    if tz.standard is None and tz.daylight is None:
        result = result.with_error(
            "VTIMEZONE must contain at least one STANDARD or DAYLIGHT "
            "sub-component (RFC 5545 §3.6.5)"
        )

    return result


# ---------------------------------------------------------------------------
# Discriminant-based bipartite relationship validation
# ---------------------------------------------------------------------------

_BREACH_THRESHOLDS = {
    "STABLE":   0.0,
    "MARGINAL": -0.1,
    "BREACH":   -0.5,
}


def validate_bipartite_relation(relation: BipartiteRelation) -> ValidationResult:
    """
    Validate a BipartiteRelation using the discriminant Δ = coherence² - 4αβ.

    Δ ≥ 0  → STABLE   (bipartite coupling intact)
    Δ ≥ -0.1 → MARGINAL (within tolerance; warning issued)
    Δ < -0.1 → BREACH  (constitutional obligation compromised; error issued)
    Δ < -0.5 → SEVERE  (systemic failure; error issued)

    Returns ValidationResult.ok() when STABLE.
    """
    result = ValidationResult.ok()
    severity = relation.breach_severity
    delta = relation.discriminant

    if severity == "STABLE":
        return result

    if severity == "MARGINAL":
        result = result.with_warning(
            f"Bipartite coupling is marginal (Δ={delta:.4f}): "
            f"{relation.organizer_uid!r} ↔ {relation.attendee_uid!r} "
            "is approaching breach threshold"
        )
    elif severity == "BREACH":
        result = result.with_error(
            f"BIPARTITE BREACH detected (Δ={delta:.4f}): "
            f"{relation.organizer_uid!r} ↔ {relation.attendee_uid!r} — "
            "constitutional obligation compromised (graph non-planar)"
        )
    else:  # SEVERE
        result = result.with_error(
            f"SEVERE BIPARTITE FAILURE (Δ={delta:.4f}): "
            f"{relation.organizer_uid!r} ↔ {relation.attendee_uid!r} — "
            "systemic decoherence detected; escalation required"
        )

    return result


def validate_trident_capsule(capsule: TridentTimeCapsule) -> ValidationResult:
    """
    Validate a TridentTimeCapsule ZKP constraint set.

    Rules:
        T1 < T2 < T3  (ascending order enforced)
        anchor_uid must be non-empty
        GCD must be > 0
    """
    result = ValidationResult.ok()

    if not capsule.anchor_uid.strip():
        result = result.with_error("TridentTimeCapsule anchor_uid must be non-empty")

    if capsule.t1.seconds <= 0:
        result = result.with_error("T1 must be a positive time constraint")

    if not (capsule.t1.seconds < capsule.t2.seconds < capsule.t3.seconds):
        result = result.with_error(
            f"Trident windows must be strictly ascending: "
            f"T1={capsule.t1.minutes:.1f}min, "
            f"T2={capsule.t2.minutes:.1f}min, "
            f"T3={capsule.t3.minutes:.1f}min"
        )

    if capsule.trident_gcd <= 0:
        result = result.with_error("Trident GCD must be positive")

    return result


# ---------------------------------------------------------------------------
# Composite validator — event + attached capsule + bipartite relation
# ---------------------------------------------------------------------------

def validate_scheduled_event(
    event: ImmutableEvent,
    relation: BipartiteRelation | None = None,
) -> ValidationResult:
    """
    Composite validator covering VEVENT + optional BipartiteRelation.

    Validates:
        1. RFC 5545 VEVENT constraints
        2. Attached TridentTimeCapsule (if present)
        3. Bipartite relation discriminant (if provided)
    """
    result = validate_event(event)

    if event.has_time_capsule:
        capsule_result = validate_trident_capsule(event.time_capsule)
        for err in capsule_result.errors:
            result = result.with_error(f"TridentCapsule: {err}")
        for warn in capsule_result.warnings:
            result = result.with_warning(f"TridentCapsule: {warn}")

    if relation is not None:
        rel_result = validate_bipartite_relation(relation)
        for err in rel_result.errors:
            result = result.with_error(f"BipartiteRelation: {err}")
        for warn in rel_result.warnings:
            result = result.with_warning(f"BipartiteRelation: {warn}")

    return result


# ---------------------------------------------------------------------------
# Module metadata
# ---------------------------------------------------------------------------

__module_metadata__ = {
    "name": "data_integrity",
    "domain": "validators",
    "problem_classification": "RFC 5545 property validation + discriminant tracking",
    "dependencies": ["structures"],
    "contracts": [],
    "thread_safe": True,
    "cost_weight": 0.25,
}


def get_module_exports() -> Dict[str, Any]:
    return {
        'validate_event': validate_event,
        'validate_alarm': validate_alarm,
        'validate_calendar': validate_calendar,
        'validate_timezone': validate_timezone,
        'validate_bipartite_relation': validate_bipartite_relation,
        'validate_trident_capsule': validate_trident_capsule,
        'validate_scheduled_event': validate_scheduled_event,
        'get_module_metadata': lambda: __module_metadata__.copy(),
    }


def initialize_module() -> bool:
    try:
        r = ValidationResult.ok()
        assert r.valid
        f = ValidationResult.fail("test error")
        assert not f.valid
        return True
    except Exception:
        return False


__all__ = [
    'validate_event',
    'validate_alarm',
    'validate_calendar',
    'validate_timezone',
    'validate_bipartite_relation',
    'validate_trident_capsule',
    'validate_scheduled_event',
    'get_module_exports',
    'initialize_module',
]

if not initialize_module():
    raise RuntimeError("Failed to initialize module: data_integrity.py")

# [EOF] - End of validators/data_integrity.py
