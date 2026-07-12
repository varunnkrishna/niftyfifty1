"""Every vote rule at, above, and below its threshold (PHASES.md Phase 4
acceptance), plus missing input -> vote 0."""

from __future__ import annotations

from pipeline.compute.votes import vote_range_thirds, vote_threshold


def test_missing_reading_votes_zero():
	assert vote_threshold(None, threshold=0.3) == 0


def test_at_and_above_positive_threshold_votes_up():
	assert vote_threshold(0.3, threshold=0.3) == 1
	assert vote_threshold(0.5, threshold=0.3) == 1


def test_below_positive_threshold_votes_flat():
	assert vote_threshold(0.29, threshold=0.3) == 0
	assert vote_threshold(0.0, threshold=0.3) == 0


def test_at_and_below_negative_threshold_votes_down():
	assert vote_threshold(-0.3, threshold=0.3) == -1
	assert vote_threshold(-0.5, threshold=0.3) == -1


def test_above_negative_threshold_votes_flat():
	assert vote_threshold(-0.29, threshold=0.3) == 0


def test_invert_flips_both_directions():
	# DXY / US10Y / USD-INR: a positive reading is bearish, not bullish.
	assert vote_threshold(0.3, threshold=0.3, invert=True) == -1
	assert vote_threshold(-0.3, threshold=0.3, invert=True) == 1
	assert vote_threshold(0.0, threshold=0.3, invert=True) == 0


def test_range_thirds_top_votes_up():
	assert vote_range_thirds("top third") == 1


def test_range_thirds_bottom_votes_down():
	assert vote_range_thirds("bottom third") == -1


def test_range_thirds_middle_votes_flat():
	assert vote_range_thirds("middle third") == 0


def test_range_thirds_missing_votes_flat():
	assert vote_range_thirds(None) == 0
