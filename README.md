# Pyics — RFC 5545 Calendar Engine with ZKP Time and Discriminant Compliance

[![Development Status](https://img.shields.io/badge/status-active%20development-orange)](https://github.com/obinexusmk2/pyics)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Architecture](https://img.shields.io/badge/architecture-single--pass%20RIFT-green.svg)](https://github.com/obinexusmk2/pyics/tree/main/docs)
[![Phase](https://img.shields.io/badge/phase-3.1.6.3-blue.svg)](https://github.com/obinexusmk2/pyics)
[![OBINexus](https://img.shields.io/badge/maintainer-OBINexus-red.svg)](https://github.com/obinexusmk2)

**Maintainer**: [OBINexus Computing](https://github.com/obinexusmk2)
**Engineering Lead**: Nnamdi Okpala
**Status**: Active Development — Phase 3.1.6.3 Single-Pass RIFT Architecture
**License**: MIT

---

## Overview

**Pyics** is a Data-Oriented Programming (DOP) iCalendar engine built on three interlocking
principles: **RFC 5545 immutable structures**, **Zero Management Procedure (ZKP) time
constraints**, and **discriminant-based bipartite compliance tracking**.

It produces, parses, validates, and transforms `.ics` calendar data with no mutable state, no
clock synchronization, and no hidden side effects. Every calendar event is a value. Every
transformation is a pure function. Every scheduling obligation is a provable constraint.

---

## Core Philosophy

### RIFT — Memory → Type → Value

Pyics follows the **RIFT** data flow model: information moves in a single direction through
three invariant layers.

```
Memory layer    →   Type layer         →   Value layer
(raw bytes)         (RFC 5545 types)       (frozen domain objects)
```

No value ever flows backward. No layer reaches across its boundary to mutate another. The
single-pass domain load order (10 → 90) encodes this invariant at the module level: a domain
at load order N may only import from domains at load order < N.

### ZKP Time — No Epochs, No Clock Sync

**Zero Management Procedure (ZKP)** treats time as a *constraint value*, not an epoch
reference. There is no concept of "current time" inside a `TridentTimeCapsule`. Time elements
are defined by their *relationship* to each other — not to any external clock.

```
T₁ < T₂ < T₃          (ordering constraint)
GCD(T₁, T₂, T₃) = τ   (scheduling atom — smallest shared scheduling unit)
T = T₁ ∪ T₂ ∪ T₃      (capsule span)
```

The trident capsule is the unit of future event scheduling. It encodes three interdependent
deadline windows: a near-term action horizon (T₁), a mid-term response window (T₂), and an
outer boundary (T₃). When elapsed time exceeds T₃, the capsule is expired.

### Discriminant — Bipartite Graph Compliance

Calendar obligations between an `ORGANIZER` and one or more `ATTENDEE` parties form a
**bipartite graph**. Pyics measures the structural integrity of this graph using the
**discriminant**:

```
coherence  =  √(α × β)
Δ          =  coherence² − 4αβ
```

Where `α` (power_alpha) represents organizer engagement and `β` (power_beta) represents
attendee response. When `Δ < 0` the graph is *non-planar* — the two parties cannot be
2-coloured without crossing — indicating a **constitutional breach** of the scheduling
obligation.

| Discriminant range | Severity | Interpretation |
|--------------------|----------|----------------|
| `Δ = 0`            | STABLE   | β = 0; obligation is one-sided; no breach |
| `−0.1 ≤ Δ < 0`    | MARGINAL | Low coupling; monitor |
| `−0.5 ≤ Δ < −0.1` | BREACH   | Graph non-planar; obligation at risk |
| `Δ < −0.5`         | SEVERE   | Deep coupling failure; escalation required |

---

## RFC 5545 Compliance

Pyics implements the VEVENT, VTIMEZONE, and VALARM components of
[RFC 5545](https://datatracker.ietf.org/doc/html/rfc5545) as frozen Python dataclasses.

| RFC Component | Pyics Type | Required Fields |
|---------------|------------|-----------------|
| `VCALENDAR`   | `ImmutableCalendar` | `PRODID`, `VERSION:2.0` |
| `VEVENT`      | `ImmutableEvent` | `UID`, `DTSTART` |
| `VTIMEZONE`   | `ImmutableTimezone` | `TZID`, `STANDARD` or `DAYLIGHT` |
| `VALARM`      | `ImmutableAlarm` | `ACTION`, `TRIGGER` |

Serialization rules enforced at `to_ics_string()`:
- Line folding at 75 octets (CRLF + SPACE continuation) per §3.1
- `DTSTART`, `DTEND` format: `YYYYMMDDTHHMMSS`
- `DURATION` format: `PTxHxMxS`
- `RRULE` serialized as `FREQ=X;COUNT=N;INTERVAL=K`
- `DTEND` and `DURATION` are mutually exclusive (RFC 5545 §3.6.1)

---

## Architecture

### Single-Pass RIFT Domain Loading

```
primitives(10) → protocols(20) → structures(30) → composition(40)
  → validators(50) → transformations(60) → registry(70) → routing(80) → safety(90)
```

**Performance targets**: boot < 100ms · memory < 50MB · abstraction overhead < 5%

### Domain Reference

| Domain | Load Order | Priority | Exposure | Compute Weight | Contents |
|--------|:----------:|:--------:|----------|:--------------:|---------|
| `primitives` | 10 | 1 | core_internal | 0.1 | Atomic operations, O(1) |
| `protocols` | 20 | 1 | version_required | 0.05 | Type-safety contracts |
| `structures` | 30 | 2 | version_required | 0.2 | RFC 5545 immutable types, ZKP, discriminant |
| `composition` | 40 | 2 | version_required | 0.3 | Lambda calculus engine |
| `validators` | 50 | 3 | version_required | 0.4 | RFC 5545 + discriminant validation |
| `transformations` | 60 | 3 | version_required | 0.6 | ICS serialization, pure event transforms |
| `registry` | 70 | 4 | version_required | 0.5 | Thread-safe component registration |
| `routing` | 80 | 4 | version_required | 0.7 | Pipeline execution coordination |
| `safety` | 90 | 5 | core_internal | 0.3 | Thread-safety, concurrency guards |

**Consolidated**: `validation/` merged into `validators`; `transforms/` and `logic/` absorbed
into `transformations` and `composition`.

### Directory Structure

```
pyics/
├── core/
│   ├── primitives/           # O(1) atomic operations, zero dependencies
│   ├── protocols/            # Interface contracts (ABC + Protocol)
│   ├── structures/           # RFC 5545 frozen dataclasses
│   │   ├── data_types.py         # EventStatus, FreqType, ActionType, RecurrenceRule
│   │   ├── zkp_time.py           # TridentTimeCapsule, BipartiteRelation, ZKPTimestamp
│   │   ├── alarm_data.py         # ImmutableAlarm (VALARM)
│   │   ├── timezone_data.py      # ImmutableTimezone (VTIMEZONE)
│   │   ├── immutable_event.py    # ImmutableEvent (VEVENT)
│   │   └── calendar_data.py      # ImmutableCalendar (VCALENDAR)
│   ├── composition/          # Lambda calculus: identity, compose, pipe, curry
│   ├── validators/           # validate_event, validate_bipartite_relation, ...
│   ├── transformations/      # to_ics_string, from_ics_lines, shift_event_time
│   │   └── legacy_transforms/
│   ├── registry/
│   ├── routing/
│   ├── safety/
│   └── ioc_registry.py
├── cli/
│   └── main.py               # CLI entry point
├── tests/
│   ├── unit/
│   │   └── core/
│   │       ├── composition/   spec_function_composition.py
│   │       ├── structures/    spec_immutable_structures.py
│   │       │                  spec_temporal_relationships.py
│   │       ├── transformations/ spec_pure_transformations.py
│   │       └── validators/    spec_data_integrity.py
│   ├── integration/
│   └── e2e/
└── __init__.py
```

---

## Installation

```bash
pip install pyics
```

```bash
# From source
git clone https://github.com/obinexusmk2/pyics.git
cd pyics
pip install -e .
pip install -e ".[dev]"
```

---

## Quick Start

### RFC 5545 Calendar — Create and Serialize

```python
from datetime import datetime, timedelta
from pyics.core.structures import (
    ImmutableEvent, ImmutableCalendar, make_calendar,
)
from pyics.core.transformations.event_transforms import (
    to_ics_string, calendar_to_ics,
)

# Create a VEVENT
event = ImmutableEvent(
    uid="standup-2026-03-01",
    dtstart=datetime(2026, 3, 1, 9, 0),
    dtend=datetime(2026, 3, 1, 9, 15),
    summary="Daily Standup",
    organizer="MAILTO:lead@example.com",
)

# Create a VCALENDAR
calendar = make_calendar("-//OBINexus//Pyics//EN").with_event(event)

# Serialize to RFC 5545 .ics text
ics_text = calendar_to_ics(calendar)
print(ics_text)
# BEGIN:VCALENDAR
# VERSION:2.0
# PRODID:-//OBINexus//Pyics//EN
# CALSCALE:GREGORIAN
# BEGIN:VEVENT
# UID:standup-2026-03-01
# DTSTART:20260301T090000
# DTEND:20260301T091500
# SUMMARY:Daily Standup
# ORGANIZER:MAILTO:lead@example.com
# ...
# END:VEVENT
# END:VCALENDAR
```

### ZKP Trident Time Capsule — Future Event Scheduling

```python
from pyics.core.structures.zkp_time import make_trident, TridentTimeCapsule
from datetime import timedelta

# Define three interdependent time windows (no clock reference)
# T1=5min (near-term), T2=15min (mid-term), T3=30min (outer boundary)
capsule = make_trident("standup-2026-03-01", t1_minutes=5, t2_minutes=15, t3_minutes=30)

print(f"GCD scheduling atom: {capsule.trident_gcd}s")
# GCD scheduling atom: 300s

# Query constraint state (elapsed time is injected, not read from a clock)
elapsed = timedelta(minutes=7)
active = capsule.active_window(elapsed)
print(f"Active window at T+7min: {active.label}")
# Active window at T+7min: T2

remaining = capsule.time_remaining(elapsed)
print(f"T2 remaining: {remaining['T2']}")
# T2 remaining: 0:08:00

print(f"Expired: {capsule.is_expired(timedelta(minutes=35))}")
# Expired: True

# Attach to an event (pure — returns new ImmutableEvent)
event_with_capsule = event.with_capsule(capsule)
```

### Discriminant — Bipartite Obligation Compliance

```python
from pyics.core.structures.zkp_time import BipartiteRelation
from pyics.core.validators.data_integrity import validate_bipartite_relation

# α = organizer engagement, β = attendee response (0.0–1.0)
relation = BipartiteRelation(
    organizer_uid="lead@example.com",
    attendee_uid="dev@example.com",
    power_alpha=0.7,
    power_beta=0.3,
)

print(f"Coherence:    {relation.coherence:.4f}")   # √(0.7 × 0.3) = 0.4583
print(f"Discriminant: {relation.discriminant:.4f}") # 0.21 - 0.84 = -0.63
print(f"Severity:     {relation.breach_severity}")  # SEVERE

result = validate_bipartite_relation(relation)
print(f"Valid: {result.valid}, Errors: {result.errors}")
# Valid: False, Errors: ('Discriminant breach SEVERE: Δ=-0.6300',)

# Stable relation (β=0 → one-sided, no breach)
stable = BipartiteRelation("org", "att", 0.5, 0.0)
print(f"Stable Δ: {stable.discriminant}")  # 0.0
print(f"Intact:   {stable.is_bipartite_intact}")  # True
```

### Lambda Calculus Composition — Pure Pipelines

```python
from pyics.core.composition import Lambda
from pyics.core.transformations.event_transforms import shift_event_time
from datetime import timedelta

# Compose pure transforms (right-to-left)
shift_and_bump = Lambda.compose(
    lambda e: e.bump_sequence(),
    shift_event_time(timedelta(hours=1)),
)

updated = shift_and_bump(event)
assert updated.dtstart.hour == 10
assert updated.sequence == 1
assert event.dtstart.hour == 9   # original unchanged

# Left-to-right pipeline
pipeline = Lambda.pipe(
    shift_event_time(timedelta(days=1)),
    lambda e: e.with_summary("Rescheduled"),
    lambda e: e.bump_sequence(),
)
rescheduled = pipeline(event)
```

### RFC 5545 Roundtrip — Parse from ICS Text

```python
from pyics.core.transformations.event_transforms import to_ics_string, from_ics_lines

ics = to_ics_string(event)
parsed = from_ics_lines(ics.splitlines())

assert parsed.uid == event.uid
assert parsed.dtstart == event.dtstart
assert parsed.summary == event.summary
```

### Validation

```python
from pyics.core.validators.data_integrity import (
    validate_event, validate_calendar, validate_scheduled_event,
)

result = validate_event(event)
print(f"Event valid: {result.valid}")

# Composite validator — checks event, capsule, and bipartite relation together
full_result = validate_scheduled_event(event, relation=relation)
print(f"Scheduled event valid: {full_result.valid}")
print(f"Errors: {full_result.errors}")
print(f"Warnings: {full_result.warnings}")
```

---

## CLI Reference

```bash
# Architecture health
pyics validate-architecture
pyics domain status [domain_name]
pyics domain load-order
pyics domain metadata primitives --format json

# Calendar operations
pyics generate   # Generate .ics files
pyics audit      # Audit existing calendars
pyics distribute # Distribute calendar files
pyics notify     # Send notifications
pyics verify     # Verify calendar integrity
```

---

## Development

```bash
# Full test suite
pytest tests/unit/                   # Unit tests (all 5 spec files)
pytest tests/unit/core/structures/   # RFC 5545 structures + ZKP
pytest tests/unit/core/transformations/  # ICS serialization roundtrip
pytest tests/unit/core/validators/   # Discriminant + RFC 5545 validation
pytest tests/integration/
```

```bash
# Architecture validation
python -c "
from pyics.core.ioc_registry import validate_architecture
print('Architecture valid:', validate_architecture())
"

# Smoke test — RFC 5545 roundtrip
python -c "
from pyics.core.structures import ImmutableEvent
from pyics.core.transformations.event_transforms import to_ics_string, from_ics_lines
from datetime import datetime
e = ImmutableEvent(uid='test', dtstart=datetime(2026,3,1,9,0), summary='Test')
rt = from_ics_lines(to_ics_string(e).splitlines())
assert rt.uid == e.uid and rt.summary == e.summary
print('RFC 5545 roundtrip OK')
"

# Smoke test — discriminant
python -c "
from pyics.core.structures.zkp_time import BipartiteRelation
r = BipartiteRelation('org', 'att', 0.7, 0.3)
assert r.discriminant < 0
print(f'Discriminant: {r.discriminant:.4f} — breach as expected')
"

# Smoke test — trident capsule
python -c "
from pyics.core.structures.zkp_time import make_trident
from datetime import timedelta
cap = make_trident('x', 5, 15, 30)
assert cap.trident_gcd == 300
assert cap.active_window(timedelta(minutes=3)).label == 'T1'
assert cap.active_window(timedelta(minutes=7)).label == 'T2'
assert cap.is_expired(timedelta(minutes=35))
print('Trident capsule OK')
"
```

### Contribution Guidelines

1. Fork and branch from `main`
2. Add modules under the correct domain directory following the 6-file pattern
   (`data_types.py`, `operations.py`, `relations.py`, `config.py`, `__init__.py`, `README.md`)
3. Register transforms via `@register_transform` — no direct cross-domain calls
4. Each domain's `config.py` must expose `get_domain_metadata()`, `validate_configuration()`,
   and `cost_metadata`
5. Maintain 90%+ test coverage with type hints throughout
6. Validate with `pyics validate-architecture` before submitting a PR

---

## Roadmap

**v1.0.0** (Current) — RFC 5545 VEVENT/VTIMEZONE/VALARM, ZKP trident capsules, discriminant
bipartite compliance, Lambda calculus composition engine, single-pass RIFT architecture.

**v2.1** — ZKP capsule chains (linked tridents), WebSocket real-time sync, REST API for
calendar obligation tracking, extended discriminant audit trails.

**v2.2** — Distributed bipartite scheduling across multi-party calendars, performance
optimization for large event graphs.

**v3.0 Preview** — AI-assisted obligation forecasting using discriminant history, blockchain
immutability proofs for high-stakes calendar obligations.

---

## License

MIT License — Copyright © 2025 OBINexus Computing

---

## Links

- **Repository**: [github.com/obinexusmk2/pyics](https://github.com/obinexusmk2/pyics)
- **Issue Tracker**: [github.com/obinexusmk2/pyics/issues](https://github.com/obinexusmk2/pyics/issues)
- **RFC 5545**: [datatracker.ietf.org/doc/html/rfc5545](https://datatracker.ietf.org/doc/html/rfc5545)
- **Architecture Spec**: [docs/DOP_FOUNDATION.md](https://github.com/obinexusmk2/pyics/blob/main/docs/DOP_FOUNDATION.md)

---

**Built by the OBINexus Engineering Team** — *When systems fail, we build our own.*
