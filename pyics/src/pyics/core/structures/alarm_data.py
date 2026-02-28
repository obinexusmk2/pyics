#!/usr/bin/env python3
"""
pyics/core/structures/alarm_data.py
RFC 5545 VALARM — Immutable Alarm Component

PROBLEM SOLVED: Immutable representation of VALARM with optional ZKP
                discriminant threshold for bipartite breach triggers.
DEPENDENCIES: structures/data_types.py (ActionType)
CONTRACT: Frozen dataclass; ACTION and TRIGGER are RFC 5545 required fields.

RFC 5545 §3.6.6 — VALARM Component:
    Required: ACTION, TRIGGER
    Optional: DURATION, REPEAT, DESCRIPTION (for DISPLAY/EMAIL actions)

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — VALARM Immutable Structure
"""

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from .data_types import ActionType


# ---------------------------------------------------------------------------
# ImmutableAlarm — VALARM component
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ImmutableAlarm:
    """
    RFC 5545 VALARM component.

    Represents a time-based trigger attached to a VEVENT.
    All instances are immutable — use with_* methods to derive variants.

    ZKP extension: *discriminant_threshold* allows alarms to fire when the
    bipartite relationship's Δ drops below a threshold (constitutional alert).

    RFC 5545 required properties:
        ACTION  : alarm action type (AUDIO, DISPLAY, EMAIL)
        TRIGGER : duration offset from event (negative = before DTSTART)

    RFC 5545 optional properties:
        DURATION  : snooze duration (requires REPEAT)
        REPEAT    : number of additional triggers (requires DURATION)
        DESCRIPTION: alarm description text (required for DISPLAY action)
    """
    action: ActionType
    trigger: timedelta                         # RFC 5545 TRIGGER (duration form)
    description: Optional[str] = None         # Required for DISPLAY alarms
    duration: Optional[timedelta] = None      # DURATION — snooze interval
    repeat: int = 0                            # REPEAT count (0 = no snooze)
    # ZKP extension — fire when BipartiteRelation.discriminant < threshold
    discriminant_threshold: Optional[float] = None

    def __post_init__(self) -> None:
        if self.repeat < 0:
            raise ValueError(f"REPEAT must be non-negative, got {self.repeat}")
        if self.repeat > 0 and self.duration is None:
            raise ValueError("DURATION is required when REPEAT > 0 (RFC 5545 §3.6.6)")
        if self.action == ActionType.DISPLAY and not self.description:
            raise ValueError("DESCRIPTION is required for DISPLAY alarms (RFC 5545 §3.6.6)")

    # -------------------------------------------------------------------
    # With-mutation helpers (return new frozen instances)
    # -------------------------------------------------------------------

    def with_description(self, description: str) -> 'ImmutableAlarm':
        return ImmutableAlarm(
            action=self.action,
            trigger=self.trigger,
            description=description,
            duration=self.duration,
            repeat=self.repeat,
            discriminant_threshold=self.discriminant_threshold,
        )

    def with_snooze(self, duration: timedelta, repeat: int) -> 'ImmutableAlarm':
        return ImmutableAlarm(
            action=self.action,
            trigger=self.trigger,
            description=self.description,
            duration=duration,
            repeat=repeat,
            discriminant_threshold=self.discriminant_threshold,
        )

    def with_discriminant_threshold(self, threshold: float) -> 'ImmutableAlarm':
        """Arm the ZKP discriminant trigger at the given Δ threshold."""
        return ImmutableAlarm(
            action=self.action,
            trigger=self.trigger,
            description=self.description,
            duration=self.duration,
            repeat=self.repeat,
            discriminant_threshold=threshold,
        )

    # -------------------------------------------------------------------
    # RFC 5545 serialisation helpers
    # -------------------------------------------------------------------

    def trigger_string(self) -> str:
        """Return RFC 5545 TRIGGER value string (duration form)."""
        total = int(self.trigger.total_seconds())
        sign = "-" if total < 0 else ""
        total = abs(total)
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        parts = "PT"
        if hours:
            parts += f"{hours}H"
        if minutes:
            parts += f"{minutes}M"
        if seconds:
            parts += f"{seconds}S"
        if parts == "PT":
            parts += "0S"
        return f"{sign}{parts}"

    def __repr__(self) -> str:
        return (
            f"ImmutableAlarm(action={self.action.value}, "
            f"trigger={self.trigger_string()!r}, "
            f"repeat={self.repeat})"
        )


# ---------------------------------------------------------------------------
# Convenience constructors
# ---------------------------------------------------------------------------

def display_alarm(description: str,
                  trigger: timedelta = timedelta(minutes=-15)) -> ImmutableAlarm:
    """Canonical DISPLAY alarm — fires *trigger* before the event."""
    return ImmutableAlarm(
        action=ActionType.DISPLAY,
        trigger=trigger,
        description=description,
    )


def audio_alarm(trigger: timedelta = timedelta(minutes=-5)) -> ImmutableAlarm:
    """Canonical AUDIO alarm — fires *trigger* before the event."""
    return ImmutableAlarm(
        action=ActionType.AUDIO,
        trigger=trigger,
    )


def breach_alarm(description: str,
                 discriminant_threshold: float = -0.1) -> ImmutableAlarm:
    """
    ZKP bipartite breach alarm.

    Fires (via external discriminant check) when Δ < *discriminant_threshold*.
    Default threshold -0.1 catches MARGINAL severity before it reaches BREACH.
    """
    return ImmutableAlarm(
        action=ActionType.DISPLAY,
        trigger=timedelta(0),   # immediate trigger (external discriminant drives it)
        description=description,
        discriminant_threshold=discriminant_threshold,
    )


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    'ImmutableAlarm',
    'display_alarm',
    'audio_alarm',
    'breach_alarm',
]

# [EOF] - End of structures/alarm_data.py
