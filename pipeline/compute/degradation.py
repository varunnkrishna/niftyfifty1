"""The missing-data degradation ladder (ORCHESTRATION §5b). Pure
classification — data_quality + whether the signal is suppressed.
"""

from __future__ import annotations


def classify_data_quality(n_missing_directional: int, n_directional_total: int, suppress_at: int) -> tuple[str, bool]:
	"""Returns (data_quality, suppressed).

	- 0 missing -> "full", not suppressed.
	- all directional inputs missing -> "outage" (ORCHESTRATION §5b item 4).
	- >= suppress_at missing -> "partial", suppressed (item 3: never publish
	  a bias computed from a minority of inputs).
	- otherwise -> "partial", not suppressed (item 1).
	"""
	if n_missing_directional == 0:
		return "full", False
	if n_missing_directional >= n_directional_total:
		return "outage", False
	return "partial", n_missing_directional >= suppress_at
