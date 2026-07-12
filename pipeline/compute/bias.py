"""bias_score aggregation and label banding (PLANNING §5, signal-config.json
`label_bands` — the conservative public-label thresholds, ORCHESTRATION §9).
"""

from __future__ import annotations


def compute_bias_score(votes: dict[str, int | None]) -> int:
	return sum(v for v in votes.values() if v is not None)


def compute_bias_label(score: int, label_bands: list[dict]) -> tuple[str, str | None]:
	"""Returns (bias_label, bias_intensity) from signal-config.json's bands."""
	for band in label_bands:
		if band["score_min"] <= score <= band["score_max"]:
			return band["bias_label"], band["intensity"]
	raise ValueError(f"score {score} is not covered by any label band in signal-config.json")
