from __future__ import annotations

from pipeline.compute.conviction import compute_conviction

CFG = {"elevated_level": 18, "spike_level": 22, "spike_delta_pct": 15}


def test_missing_vix_skips_damping():
	assert compute_conviction(None, None, CFG) == "normal"


def test_calm_vix_is_normal():
	assert compute_conviction(14.8, 0.6, CFG) == "normal"


def test_elevated_level_reduces_conviction():
	assert compute_conviction(18.0, 1.0, CFG) == "reduced"
	assert compute_conviction(20.0, None, CFG) == "reduced"


def test_below_elevated_is_normal():
	assert compute_conviction(17.9, 5.0, CFG) == "normal"


def test_spike_delta_reduces_conviction_even_below_elevated_level():
	assert compute_conviction(16.0, 16.0, CFG) == "reduced"


def test_spike_delta_below_threshold_stays_normal():
	assert compute_conviction(16.0, 14.9, CFG) == "normal"
