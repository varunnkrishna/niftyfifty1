"""VIX conviction dampener (PLANNING §5, ORCHESTRATION §5b item 2). India
VIX never votes on direction — it only ever damps conviction. Missing VIX
skips damping entirely (conviction stays "normal"), it does not suppress
the signal by itself.
"""

from __future__ import annotations

from typing import Literal

Conviction = Literal["normal", "reduced"]


def compute_conviction(vix_level: float | None, vix_delta_pct: float | None, dampener_config: dict) -> Conviction:
	if vix_level is None:
		return "normal"

	if vix_level >= dampener_config["elevated_level"]:
		return "reduced"

	spike_delta = dampener_config.get("spike_delta_pct")
	if spike_delta is not None and vix_delta_pct is not None and vix_delta_pct >= spike_delta:
		return "reduced"

	return "normal"
