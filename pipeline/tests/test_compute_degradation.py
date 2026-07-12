"""4 missing directional inputs -> suppressed; 3 missing -> published
partial (PHASES.md Phase 4 acceptance)."""

from __future__ import annotations

from pipeline.compute.degradation import classify_data_quality


def test_zero_missing_is_full():
	assert classify_data_quality(0, 9, suppress_at=4) == ("full", False)


def test_three_missing_is_partial_not_suppressed():
	assert classify_data_quality(3, 9, suppress_at=4) == ("partial", False)


def test_four_missing_is_partial_and_suppressed():
	assert classify_data_quality(4, 9, suppress_at=4) == ("partial", True)


def test_more_than_four_missing_is_still_suppressed():
	assert classify_data_quality(7, 9, suppress_at=4) == ("partial", True)


def test_all_missing_is_outage():
	assert classify_data_quality(9, 9, suppress_at=4) == ("outage", False)
