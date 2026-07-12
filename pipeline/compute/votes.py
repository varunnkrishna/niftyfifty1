"""Vote rule functions (PLANNING §5, ORCHESTRATION §9's signal-config.json).
Pure functions only — no I/O, no fetching. Every threshold is a parameter,
never a literal, so tuning data/signal-config.json changes behavior with
zero code edits (PHASES.md Phase 4 acceptance).

Sign convention: `invert=False` means a positive reading votes +1 and a
negative reading votes -1 (e.g. GIFT Nifty up = bullish = +1). `invert=True`
flips both (e.g. rising DXY is bearish for India = -1) — this mirrors
signal-config.json's own `invert` flag per input exactly.
"""

from __future__ import annotations

Vote = int | None  # -1, 0, or +1; None only ever means "input unavailable"


def vote_threshold(reading: float | None, threshold: float, invert: bool = False) -> int:
	"""The one shared rule shape behind threshold_pct / threshold_delta /
	threshold_absolute (they differ only in what `reading` and `threshold`
	are measured in, not in the comparison logic itself)."""
	if reading is None:
		return 0
	sign = -1 if invert else 1
	if reading >= threshold:
		return 1 * sign
	if reading <= -threshold:
		return -1 * sign
	return 0


def vote_range_thirds(position: str | None) -> int:
	"""prev_close_in_range: top third of the day's range = +1 (momentum),
	bottom third = -1, middle third (or missing) = 0."""
	return {"top third": 1, "bottom third": -1}.get(position or "", 0)
