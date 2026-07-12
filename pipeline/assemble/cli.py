"""Thin entrypoint: `python -m pipeline.assemble.cli <date|--all>`.

Reads data/days/<date>.json, assembles it, writes the MDX render artifact
to src/content/docs/YYYY/MM/DD.mdx. Side effects (file I/O) live only here —
assembler.py itself is pure (ORCHESTRATION/CLAUDE.md conventions).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from pipeline.assemble.assembler import assemble_mdx, content_path

REPO_ROOT = Path(__file__).resolve().parents[2]
DAYS_DIR = REPO_ROOT / "data" / "days"


def assemble_one(iso_date: str) -> Path:
	raw = json.loads((DAYS_DIR / f"{iso_date}.json").read_text())
	mdx = assemble_mdx(raw)
	out_path = REPO_ROOT / content_path(iso_date)
	out_path.parent.mkdir(parents=True, exist_ok=True)
	out_path.write_text(mdx)
	return out_path


def main(argv: list[str]) -> int:
	if not argv:
		print("usage: python -m pipeline.assemble.cli <YYYY-MM-DD | --all>", file=sys.stderr)
		return 2

	if argv[0] == "--all":
		dates = sorted(p.stem for p in DAYS_DIR.glob("*.json"))
	else:
		dates = argv

	for iso_date in dates:
		out_path = assemble_one(iso_date)
		print(f"assembled {iso_date} -> {out_path.relative_to(REPO_ROOT)}")

	return 0


if __name__ == "__main__":
	raise SystemExit(main(sys.argv[1:]))
