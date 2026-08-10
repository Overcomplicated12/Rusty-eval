"""Manual migration-effort records, kept separate from harness debugging."""

from __future__ import annotations

from .models import HumanEffortCategory, HumanIntervention


def record_intervention(*, category: HumanEffortCategory, minutes: float, description: str, unit_id: str, recorded_by: str | None = None) -> HumanIntervention:
    if minutes < 0:
        raise ValueError("manual effort minutes must not be negative")
    if not description.strip():
        raise ValueError("manual effort requires a description")
    return HumanIntervention(category, minutes, description, unit_id, recorded_by)
