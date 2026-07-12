"""Retry/backoff/fallback orchestration (ORCHESTRATION §5a):
3 attempts per source, exponential backoff 5s/15s/45s, then the fallback
source (same retry treatment), then an honest missing-marker. Never raises —
a fetch that exhausts every option becomes `unavailable`, not a crash, so a
single flaky source can never take down a whole pipeline run (CLAUDE.md
rule 4: "a day page always publishes").
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")

DEFAULT_BACKOFFS_SECONDS = (5, 15, 45)


@dataclass
class FetchOutcome:
	metric: str
	value: T | None
	source: str | None  # name of the source that actually succeeded
	unavailable: bool
	errors: list[str]


def _try_source(name: str, fn: Callable[[], T], backoffs: tuple[int, ...], sleep_fn: Callable[[float], None]) -> tuple[T | None, list[str]]:
	errors: list[str] = []
	for attempt, delay in enumerate((0, *backoffs)):
		if delay:
			sleep_fn(delay)
		try:
			return fn(), errors
		except Exception as exc:  # noqa: BLE001 - any source failure is a soft failure here
			errors.append(f"{name} attempt {attempt + 1}: {exc}")
	return None, errors


def fetch_with_fallback(
	metric: str,
	primary: tuple[str, Callable[[], T]],
	fallback: tuple[str, Callable[[], T]] | None = None,
	backoffs: tuple[int, ...] = DEFAULT_BACKOFFS_SECONDS,
	sleep_fn: Callable[[float], None] = time.sleep,
) -> FetchOutcome:
	primary_name, primary_fn = primary
	value, errors = _try_source(primary_name, primary_fn, backoffs, sleep_fn)
	if value is not None:
		return FetchOutcome(metric=metric, value=value, source=primary_name, unavailable=False, errors=errors)

	if fallback is not None:
		fallback_name, fallback_fn = fallback
		value, fallback_errors = _try_source(fallback_name, fallback_fn, backoffs, sleep_fn)
		errors = errors + fallback_errors
		if value is not None:
			return FetchOutcome(metric=metric, value=value, source=fallback_name, unavailable=False, errors=errors)

	return FetchOutcome(metric=metric, value=None, source=None, unavailable=True, errors=errors)
