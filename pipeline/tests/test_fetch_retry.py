"""Retry/fallback/missing-marker behavior (PHASES.md Phase 3 acceptance):
forcing a primary source to fail must demonstrably exercise the fallback,
then the missing-marker path — all without hitting the network."""

from __future__ import annotations

from pipeline.fetch.retry import fetch_with_fallback


def _no_sleep(_seconds: float) -> None:
	pass


def test_primary_success_never_calls_fallback():
	calls = {"primary": 0, "fallback": 0}

	def primary():
		calls["primary"] += 1
		return 42

	def fallback():
		calls["fallback"] += 1
		return 99

	outcome = fetch_with_fallback("m", ("primary", primary), ("fallback", fallback), backoffs=(1, 1), sleep_fn=_no_sleep)

	assert outcome.value == 42
	assert outcome.source == "primary"
	assert outcome.unavailable is False
	assert calls == {"primary": 1, "fallback": 0}


def test_primary_failure_exercises_fallback():
	attempts = {"primary": 0, "fallback": 0}

	def primary():
		attempts["primary"] += 1
		raise ConnectionError("primary down")

	def fallback():
		attempts["fallback"] += 1
		return "fallback-value"

	outcome = fetch_with_fallback("m", ("primary", primary), ("fallback", fallback), backoffs=(1, 1), sleep_fn=_no_sleep)

	assert outcome.value == "fallback-value"
	assert outcome.source == "fallback"
	assert outcome.unavailable is False
	# 3 attempts on primary (1 initial + 2 backoff retries) before falling through.
	assert attempts["primary"] == 3
	assert attempts["fallback"] == 1
	assert len(outcome.errors) == 3


def test_primary_and_fallback_both_failing_marks_missing():
	def always_fails():
		raise TimeoutError("network unreachable")

	outcome = fetch_with_fallback("m", ("primary", always_fails), ("fallback", always_fails), backoffs=(1, 1), sleep_fn=_no_sleep)

	assert outcome.value is None
	assert outcome.source is None
	assert outcome.unavailable is True
	assert len(outcome.errors) == 6  # 3 attempts x 2 sources


def test_no_fallback_configured_marks_missing_after_primary_exhausted():
	def always_fails():
		raise ValueError("no data")

	outcome = fetch_with_fallback("m", ("primary", always_fails), fallback=None, backoffs=(1, 1), sleep_fn=_no_sleep)

	assert outcome.unavailable is True
	assert outcome.source is None


def test_fallback_recovers_after_primary_intermittent_failures():
	"""A primary that fails twice then succeeds should still resolve via
	primary — the retry loop, not just the fallback, must actually work."""
	attempts = {"n": 0}

	def flaky_primary():
		attempts["n"] += 1
		if attempts["n"] < 3:
			raise ConnectionError("transient")
		return "recovered"

	outcome = fetch_with_fallback("m", ("primary", flaky_primary), backoffs=(1, 1, 1), sleep_fn=_no_sleep)

	assert outcome.value == "recovered"
	assert outcome.source == "primary"
	assert outcome.unavailable is False
