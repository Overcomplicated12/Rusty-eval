"""Measured-only telemetry aggregation for experiment records."""

from __future__ import annotations

from collections import defaultdict

from .models import AgentAttempt, TokenSource, TokenUsage


def aggregate_tokens(attempts: list[AgentAttempt]) -> TokenUsage:
    usages = [attempt.response.token_usage for attempt in attempts if attempt.response is not None]
    reported = [usage for usage in usages if usage.source is TokenSource.PROVIDER_REPORTED]
    estimated = [usage for usage in usages if usage.source is TokenSource.LOCAL_ESTIMATE]
    usable = [usage for usage in usages if usage.source in (TokenSource.PROVIDER_REPORTED, TokenSource.LOCAL_ESTIMATE)]
    if not usable:
        return TokenUsage()
    if reported and not estimated:
        source = TokenSource.PROVIDER_REPORTED
    elif estimated and not reported:
        source = TokenSource.LOCAL_ESTIMATE
    else:
        # A mixed aggregate cannot honestly claim one provenance category.
        source = TokenSource.UNAVAILABLE
    def total(field: str) -> int | None:
        values = [getattr(usage, field) for usage in usable]
        return sum(value for value in values if value is not None) if any(value is not None for value in values) else None
    return TokenUsage(total("input_tokens"), total("output_tokens"), total("total_tokens"), source)


def attempt_counts(attempts: list[AgentAttempt]) -> dict[str, int]:
    counts: dict[str, int] = defaultdict(int)
    for attempt in attempts:
        counts[attempt.purpose.value] += 1
    return dict(sorted(counts.items()))


def agent_wall_seconds(attempts: list[AgentAttempt]) -> float | None:
    values = [attempt.response.elapsed_seconds for attempt in attempts if attempt.response and attempt.response.elapsed_seconds is not None]
    return sum(values) if values else None
