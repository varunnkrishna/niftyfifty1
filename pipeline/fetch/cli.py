"""Thin entrypoint: `python -m pipeline.fetch.cli <YYYY-MM-DD>`.

Writes the raw-fetch JSON to data/raw/<date>.json. Reads the prior day's
sidecar JSON from data/days/ if present (feeds prev_close_in_range).
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

from pipeline.fetch.raw_output import build_raw_fetch

REPO_ROOT = Path(__file__).resolve().parents[2]
DAYS_DIR = REPO_ROOT / "data" / "days"
RAW_DIR = REPO_ROOT / "data" / "raw"


def _load_prev_day_sidecar(iso_date: str) -> dict | None:
	prev = date.fromisoformat(iso_date) - timedelta(days=1)
	path = DAYS_DIR / f"{prev.isoformat()}.json"
	if not path.exists():
		return None
	return json.loads(path.read_text())


def main(argv: list[str]) -> int:
	if not argv:
		print("usage: python -m pipeline.fetch.cli <YYYY-MM-DD>", file=sys.stderr)
		return 2

	iso_date = argv[0]
	prev_day_sidecar = _load_prev_day_sidecar(iso_date)
	raw = build_raw_fetch(iso_date, prev_day_sidecar)

	RAW_DIR.mkdir(parents=True, exist_ok=True)
	out_path = RAW_DIR / f"{iso_date}.json"
	out_path.write_text(json.dumps(raw, indent="\t", sort_keys=True))

	populated = sum(1 for m in raw["metrics"].values() if not m["unavailable"])
	print(f"wrote {out_path.relative_to(REPO_ROOT)} — {populated}/{len(raw['metrics'])} metrics populated, {len(raw['news'])} news items, {len(raw['rss_warnings'])} RSS warnings")
	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))
