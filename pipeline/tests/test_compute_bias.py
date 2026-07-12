from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.compute.bias import compute_bias_label, compute_bias_score

CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "signal-config.json"
BANDS = json.loads(CONFIG_PATH.read_text())["label_bands"]["bands"]


def test_bias_score_sums_available_votes_only():
	votes = {"a": 1, "b": -1, "c": None, "d": 1}
	assert compute_bias_score(votes) == 1


@pytest.mark.parametrize(
	"score,expected_label,expected_intensity",
	[
		(9, "Long", "Strongly"),
		(5, "Long", "Strongly"),
		(4, "Long", "Mildly"),
		(2, "Long", "Mildly"),
		(1, "Neutral", None),
		(0, "Neutral", None),
		(-1, "Neutral", None),
		(-2, "Short", "Mildly"),
		(-4, "Short", "Mildly"),
		(-5, "Short", "Strongly"),
		(-9, "Short", "Strongly"),
	],
)
def test_label_bands_boundaries(score, expected_label, expected_intensity):
	label, intensity = compute_bias_label(score, BANDS)
	assert label == expected_label
	assert intensity == expected_intensity


def test_score_outside_bands_raises():
	with pytest.raises(ValueError):
		compute_bias_label(999, BANDS)
