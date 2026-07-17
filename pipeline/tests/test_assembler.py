"""Assembler determinism and the premarket-immutability property
(PHASES.md Phase 2 acceptance; ORCHESTRATION §3, §6b)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
import yaml

from pipeline.assemble.assembler import assemble_mdx

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "data" / "days"
ALL_FIXTURES = sorted(p.stem for p in FIXTURES_DIR.glob("*.json"))


def _frontmatter(mdx_text: str) -> dict:
	_, fm_text, _ = mdx_text.split("---", 2)
	return yaml.safe_load(fm_text)


@pytest.mark.parametrize("iso_date", ALL_FIXTURES)
def test_assembling_same_json_twice_is_byte_identical(iso_date):
	raw = json.loads((FIXTURES_DIR / f"{iso_date}.json").read_text())
	first = assemble_mdx(raw)
	second = assemble_mdx(copy.deepcopy(raw))
	assert first == second


@pytest.mark.parametrize("iso_date", ALL_FIXTURES)
def test_assembling_is_stable_across_key_order(iso_date):
	"""Same data, different JSON key order in the input -> identical MDX."""
	raw = json.loads((FIXTURES_DIR / f"{iso_date}.json").read_text())
	reordered = json.loads(json.dumps(raw, sort_keys=True))
	assert assemble_mdx(raw) == assemble_mdx(reordered)


def test_eod_write_changes_only_eod_region_and_meta():
	"""Assembling the awaiting-EOD fixture, then assembling the same day with
	an EOD block appended, must leave `premarket` byte-for-byte identical —
	the mechanical form of CLAUDE.md rule 2 / ORCHESTRATION §3's immutability
	rule, verified by diffing the parsed frontmatter directly.
	"""
	# Use an awaiting-EOD fixture (live days get eod_written=True after the
	# close run; 2026-07-07 is the stable pre-EOD shell fixture).
	before_raw = json.loads((FIXTURES_DIR / "2026-07-07.json").read_text())
	assert before_raw["eod_written"] is False

	after_raw = copy.deepcopy(before_raw)
	after_raw["eod_written"] = True
	after_raw["eod"] = {
		"nifty_close": {"value": 24601.2, "delta_pct": 0.09},
		"sensex_close": {"value": 80920.4, "delta_pct": 0.11},
		"banknifty_close": {"value": 55340.6, "delta_pct": 0.24},
		"advance_decline": "1,720 advances / 1,310 declines",
		"sector_leaders": ["Auto"],
		"sector_laggards": ["FMCG"],
		"conclusion": "Nifty closed up 0.09% at 24,601, a quiet grind that held the morning's Mildly Long call.",
		"news": [
			{
				"headline_reworded": "Auto stocks lead a quiet close as festive-season demand hopes build",
				"why_it_matters": "Auto was the session's clearest sector story.",
				"source_name": "Moneycontrol",
				"source_url": "https://www.moneycontrol.com/news/business/markets/auto-festive-demand-close",
				"timestamp": "2026-07-07T15:45:00+05:30",
			}
		],
	}

	before_mdx = assemble_mdx(before_raw)
	after_mdx = assemble_mdx(after_raw)

	before_fm = _frontmatter(before_mdx)
	after_fm = _frontmatter(after_mdx)

	# The load-bearing assertion: premarket is untouched by the EOD write.
	assert before_fm["premarket"] == after_fm["premarket"]
	assert before_fm["date"] == after_fm["date"]
	assert before_fm["type"] == after_fm["type"]
	assert before_fm["data_quality"] == after_fm["data_quality"]
	assert before_fm["missing"] == after_fm["missing"]

	# What's allowed to change: eod region + eod_written + title/description meta.
	assert before_fm["eod_written"] is False
	assert after_fm["eod_written"] is True
	assert "eod" not in before_fm
	assert after_fm["eod"]["conclusion"].startswith("Nifty closed up 0.09%")
	assert before_fm["title"] != after_fm["title"]  # "outlook" -> "Nifty & Sensex"
	assert before_fm["description"] != after_fm["description"]
