#!/usr/bin/env python3
"""
pyics/core/structures/zkp_time.py
Zero Management Procedure (ZKP) Time System

PROBLEM SOLVED: Time-bound scheduling without epochs, clock sync, or time steps.
                Bipartite relationship tracking with discriminant breach detection.
DEPENDENCIES: stdlib only (dataclasses, math, datetime)
CONTRACT: Immutable frozen dataclasses. Time is a constraint value, not a reference.

Philosophy (Lapis Lambda Calculus / MMUKO-OS):
  - No epochs, no time steps, no clock synchronisations
  - T ≠ T'  (time is independent of its derivative)
  - T_i ∈ T  (time as elements of a constraint set)
  - Trident: three interdependent windows T1 < T2 < T3, GCD-related
  - Bipartite discriminant Δ = coherence² - 4αβ
    • Δ ≥ 0 → stable bipartite coupling (graph is 2-colorable)
    • Δ < 0 → non-planar (constitutional breach — escalation required)

Author: OBINexus Engineering Team / Nnamdi Okpala
Architecture: Single-Pass RIFT System — Memory → Type → Value
Phase: 3.1.6.3 — ZKP Time Capsule + Discriminant Tracking
"""

import math
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# GCD helper (pure function)
# ---------------------------------------------------------------------------

def _gcd(a: int, b: int) -> int:
    """Euclidean GCD — pure, no state."""
    while b:
        a, b = b, a % b
    return a


def _gcd_many(*values: int) -> int:
    """GCD of multiple values."""
    result = values[0]
    for v in values[1:]:
        result = _gcd(result, v)
    return result


# ---------------------------------------------------------------------------
# ZKPTimestamp — time as a constraint value
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ZKPTimestamp:
    """
    Time expressed as a constraint offset, not an epoch reference.

    ZKP principle: T_i ∈ T  (this timestamp is an element of a time set).
    The *value* encodes how much time is allocated; no wall-clock required.

    Attributes:
        value    : time window as a timedelta constraint
        label    : human label (e.g. "T1", "T2", "T3")
        gcd_factor: GCD relationship denominator to sibling timestamps (seconds)
    """
    value: timedelta
    label: str
    gcd_factor: int = 1   # filled by TridentTimeCapsule on construction

    @property
    def seconds(self) -> int:
        """Total seconds in this constraint window."""
        return int(self.value.total_seconds())

    @property
    def minutes(self) -> float:
        """Total minutes in this constraint window."""
        return self.value.total_seconds() / 60.0

    def __repr__(self) -> str:
        return f"ZKPTimestamp({self.label}={self.minutes:.1f}min, gcd={self.gcd_factor}s)"


# ---------------------------------------------------------------------------
# TridentTimeCapsule — three interdependent time windows
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TridentTimeCapsule:
    """
    Three interdependent ZKP time windows for future event scheduling.

    The trident structure (T1 < T2 < T3) encodes parallel, GCD-related
    time horizons for a single scheduling obligation:

        T = T1 ∪ T2 ∪ T3   (time as a constraint set, not a timeline)
        GCD(T1, T2, T3) → the fundamental scheduling unit

    No epochs. No clock synchronisation. Time flows *down* — once a window
    passes, it is consumed and cannot be recovered.

    Attributes:
        t1          : near-term constraint (e.g. 5 min — act now)
        t2          : mid-term constraint  (e.g. 15 min — act soon)
        t3          : long-term constraint (e.g. 30 min — act today)
        anchor_uid  : UID of the reference VEVENT this capsule is attached to
    """
    t1: ZKPTimestamp
    t2: ZKPTimestamp
    t3: ZKPTimestamp
    anchor_uid: str

    # -------------------------------------------------------------------
    # Derived properties (ZKP invariants)
    # -------------------------------------------------------------------

    @property
    def trident_gcd(self) -> int:
        """GCD of all three window values in seconds — the scheduling atom."""
        return _gcd_many(self.t1.seconds, self.t2.seconds, self.t3.seconds)

    @property
    def total_span(self) -> timedelta:
        """Total time span covered by the trident (largest window)."""
        return self.t3.value

    @property
    def windows(self) -> Tuple[ZKPTimestamp, ZKPTimestamp, ZKPTimestamp]:
        """Ordered tuple of the three time windows (near → far)."""
        return (self.t1, self.t2, self.t3)

    # -------------------------------------------------------------------
    # Constraint operations (pure functions)
    # -------------------------------------------------------------------

    def time_remaining(self, elapsed: timedelta) -> Dict[str, Optional[timedelta]]:
        """
        Compute remaining time in each window given *elapsed* time.

        A window returns None when it has been fully consumed.
        Time only flows forward — no negative remaining values.
        """
        def remaining(window: ZKPTimestamp) -> Optional[timedelta]:
            r = window.value - elapsed
            return r if r.total_seconds() > 0 else None

        return {
            self.t1.label: remaining(self.t1),
            self.t2.label: remaining(self.t2),
            self.t3.label: remaining(self.t3),
        }

    def active_window(self, elapsed: timedelta) -> Optional[ZKPTimestamp]:
        """Return the smallest window that has not yet been consumed."""
        for w in self.windows:
            if (w.value - elapsed).total_seconds() > 0:
                return w
        return None

    def is_expired(self, elapsed: timedelta) -> bool:
        """True when all three windows are consumed."""
        return self.active_window(elapsed) is None

    def __repr__(self) -> str:
        return (
            f"TridentTimeCapsule(anchor={self.anchor_uid!r}, "
            f"T1={self.t1.minutes:.0f}min, T2={self.t2.minutes:.0f}min, "
            f"T3={self.t3.minutes:.0f}min, GCD={self.trident_gcd}s)"
        )


# ---------------------------------------------------------------------------
# Factory — canonical trident (5 / 15 / 30 min)
# ---------------------------------------------------------------------------

def make_trident(anchor_uid: str,
                 t1_minutes: int = 5,
                 t2_minutes: int = 15,
                 t3_minutes: int = 30) -> TridentTimeCapsule:
    """
    Construct a TridentTimeCapsule with GCD-computed factors.

    Default windows (from the ZKP lecture):
        T1 = 5 min  (near-term)
        T2 = 15 min (mid-term, GCD(5,15) = 5)
        T3 = 30 min (long-term, GCD(5,15,30) = 5)
    """
    t1_sec = t1_minutes * 60
    t2_sec = t2_minutes * 60
    t3_sec = t3_minutes * 60
    g = _gcd_many(t1_sec, t2_sec, t3_sec)

    t1 = ZKPTimestamp(timedelta(minutes=t1_minutes), "T1", g)
    t2 = ZKPTimestamp(timedelta(minutes=t2_minutes), "T2", g)
    t3 = ZKPTimestamp(timedelta(minutes=t3_minutes), "T3", g)
    return TridentTimeCapsule(t1=t1, t2=t2, t3=t3, anchor_uid=anchor_uid)


# ---------------------------------------------------------------------------
# BipartiteRelation — discriminant tracking for ORGANIZER ↔ ATTENDEE
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BipartiteRelation:
    """
    Discriminant-based bipartite relationship tracker.

    Models a constitutional obligation between two parties (e.g. ORGANIZER
    and ATTENDEE in a VEVENT) as a bipartite graph coupling.

    Mathematics (from the article):
        coherence = √(α × β)
        Δ = coherence² - 4αβ = αβ - 4αβ = -3αβ   [simplified]

    However, the full formulation used here is:
        Δ = coherence² - 4αβ
          = (α·β) - 4αβ
          = -3αβ

    This is always ≤ 0 for real α, β ∈ (0, 1), meaning bipartite coupling
    between two parties with non-zero energy will always have Δ < 0.

    In practice, we track the *magnitude* of Δ to measure breach severity:
        Δ → 0     : marginal (coupling near equilibrium, α ≈ β ≈ 0)
        Δ < -0.5  : breach (significant power imbalance)
        Δ < -2.0  : severe (one party has absorbed all agency)

    Attributes:
        organizer_uid : identifier for party in Set U (the institution)
        attendee_uid  : identifier for party in Set V (the citizen)
        power_alpha   : energy of the organizer (0.0 – 1.0)
        power_beta    : energy of the attendee  (0.0 – 1.0)
    """
    organizer_uid: str
    attendee_uid: str
    power_alpha: float   # α — organizer energy
    power_beta: float    # β — attendee energy

    def __post_init__(self) -> None:
        object.__setattr__(self, 'power_alpha',
                           max(0.0, min(1.0, self.power_alpha)))
        object.__setattr__(self, 'power_beta',
                           max(0.0, min(1.0, self.power_beta)))

    # -------------------------------------------------------------------
    # Core discriminant mathematics
    # -------------------------------------------------------------------

    @property
    def coherence(self) -> float:
        """√(α × β) — coupling strength between the two parties."""
        return math.sqrt(self.power_alpha * self.power_beta)

    @property
    def discriminant(self) -> float:
        """
        Δ = coherence² - 4αβ

        Δ < 0 → the bipartite structure is non-planar (odd-cycle present).
        The more negative Δ is, the more severe the power imbalance.
        """
        c_sq = self.coherence ** 2   # == α·β
        return c_sq - 4 * self.power_alpha * self.power_beta

    @property
    def is_bipartite_intact(self) -> bool:
        """True when Δ ≥ 0 — graph is 2-colorable, coupling is stable."""
        return self.discriminant >= 0

    @property
    def breach_severity(self) -> str:
        """
        Qualitative severity of the discriminant breach.

        STABLE   : Δ ≥ 0
        MARGINAL : -0.1 ≤ Δ < 0
        BREACH   : -0.5 ≤ Δ < -0.1
        SEVERE   : Δ < -0.5
        """
        d = self.discriminant
        if d >= 0:
            return "STABLE"
        if d >= -0.1:
            return "MARGINAL"
        if d >= -0.5:
            return "BREACH"
        return "SEVERE"

    # -------------------------------------------------------------------
    # State transitions (pure — return new instance)
    # -------------------------------------------------------------------

    def with_response(self, response_fraction: float = 1.0) -> 'BipartiteRelation':
        """
        Simulate an attendee responding, restoring their power level.

        *response_fraction* ∈ [0, 1] — fraction of β power restored.
        Returns a new BipartiteRelation with updated β.
        """
        new_beta = min(1.0, self.power_beta + response_fraction * (1.0 - self.power_beta))
        return BipartiteRelation(
            organizer_uid=self.organizer_uid,
            attendee_uid=self.attendee_uid,
            power_alpha=self.power_alpha,
            power_beta=new_beta,
        )

    def decay(self, alpha_decay: float = 0.1, beta_decay: float = 0.1) -> 'BipartiteRelation':
        """
        Apply time-based power decay to both parties.

        Call periodically (e.g. once per day with no response) to model
        the progressive loss of coherence when a party goes silent.
        """
        return BipartiteRelation(
            organizer_uid=self.organizer_uid,
            attendee_uid=self.attendee_uid,
            power_alpha=max(0.0, self.power_alpha - alpha_decay),
            power_beta=max(0.0, self.power_beta - beta_decay),
        )

    def __repr__(self) -> str:
        return (
            f"BipartiteRelation(α={self.power_alpha:.2f}, β={self.power_beta:.2f}, "
            f"Δ={self.discriminant:.4f}, severity={self.breach_severity})"
        )


# ---------------------------------------------------------------------------
# Module exports
# ---------------------------------------------------------------------------

__all__ = [
    'ZKPTimestamp',
    'TridentTimeCapsule',
    'BipartiteRelation',
    'make_trident',
]

# [EOF] - End of structures/zkp_time.py
