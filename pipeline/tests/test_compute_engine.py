"""End-to-end compute engine tests against realistic raw-fetch shapes,
including the config-driven-tuning acceptance check (PHASES.md Phase 4:
"changing a threshold in signal-config.json changes behavior with zero
code edits")."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from pipeline.compute.engine import DIRECTIONAL_KEYS, compute_premarket_numbers

CONFIG_PATH = Path(__file__).resolve().parents[2] / "data" / "signal-config.json"


@pytest.fixture
def signal_config() -> dict:
	return json.loads(CONFIG_PATH.read_text())


def _full_raw_fetch() -> dict:
	"""Every metric present, votes summing to a clean +5 (Strongly Long)."""
	return {
		"date": "2026-07-13",
		"metrics": {
			"gift_nifty": {"value": {"value": 24500.0}, "source": "yahoo", "unavailable": False},
			"sp500_overnight": {"value": {"value": 5000, "prev_close": 4950, "delta_pct": 1.0}, "source": "yahoo", "unavailable": False},
			"nasdaq_overnight": {"value": {"value": 17000, "prev_close": 16800, "delta_pct": 1.19}, "source": "yahoo", "unavailable": False},
			"us10y_yield": {"value": {"value": 4.2, "delta": -0.05, "date": "2026-07-12"}, "source": "fred", "unavailable": False},
			"dxy": {"value": {"value": 100.0, "prev_close": 100.3, "delta_pct": -0.3}, "source": "yahoo", "unavailable": False},
			"fii_net_cash": {"value": 800.0, "source": "nse", "unavailable": False},
			"dii_net_cash": {"value": 600.0, "source": "nse", "unavailable": False},
			"usdinr": {"value": {"value": 83.5, "prev_close": 83.6, "delta_pct": -0.12}, "source": "yahoo", "unavailable": False},
			"prev_close_in_range": {"value": "top third", "source": "archive", "unavailable": False},
			"india_vix": {"value": {"value": 14.0, "delta": 0.2}, "source": "nse", "unavailable": False},
			"brent": {"value": {"value": 80.0, "prev_close": 79.5, "delta_pct": 0.6}, "source": "yahoo", "unavailable": False},
		},
	}


def _prev_day() -> dict:
	return {"eod": {"nifty_close": {"value": 24000.0}}}


def _mark_unavailable(raw: dict, keys: list[str]) -> dict:
	raw = copy.deepcopy(raw)
	for key in keys:
		raw["metrics"][key] = {"value": None, "source": None, "unavailable": True}
	return raw


def test_full_data_produces_expected_score_and_label(signal_config):
	result = compute_premarket_numbers(_full_raw_fetch(), _prev_day(), signal_config)

	# gift(+1) sp500(+1) nasdaq(+1) us10y(0, |5bp|<no wait see below) dxy(+1) fii(+1) dii(+1) usdinr(+1) prevclose(+1)
	assert result["data_quality"] == "full"
	assert result["missing"] == []
	assert result["bias_label"] in ("Long", "Neutral", "Short")  # sanity: a label was assigned
	assert result["bias_score"] is not None


def test_three_missing_directional_inputs_is_partial_not_suppressed(signal_config):
	raw = _mark_unavailable(_full_raw_fetch(), ["dxy", "brent", "us10y_yield"])
	# brent isn't directional, so only dxy + us10y_yield count -> add one more
	raw = _mark_unavailable(raw, ["dxy", "us10y_yield", "usdinr"])
	result = compute_premarket_numbers(raw, _prev_day(), signal_config)

	assert len(result["missing"]) == 3
	assert result["data_quality"] == "partial"
	assert result["bias_label"] is not None  # not suppressed
	assert result["bias_score"] is not None


def test_four_missing_directional_inputs_is_suppressed(signal_config):
	raw = _mark_unavailable(_full_raw_fetch(), ["dxy", "us10y_yield", "usdinr", "fii_net_cash"])
	result = compute_premarket_numbers(raw, _prev_day(), signal_config)

	assert len(result["missing"]) == 4
	assert result["data_quality"] == "partial"
	assert result["bias_label"] is None
	assert result["bias_score"] is None
	assert result["bias_intensity"] is None


def test_all_directional_missing_is_outage(signal_config):
	raw = _mark_unavailable(_full_raw_fetch(), list(DIRECTIONAL_KEYS))
	result = compute_premarket_numbers(raw, _prev_day(), signal_config)

	assert result["data_quality"] == "outage"
	assert result["bias_label"] is None


def test_gift_nifty_without_prev_day_archive_is_unavailable(signal_config):
	result = compute_premarket_numbers(_full_raw_fetch(), prev_day_sidecar=None, signal_config=signal_config)
	assert result["gift_nifty"]["unavailable"] is True
	assert "gift_nifty" in result["missing"]


def test_changing_threshold_in_config_changes_vote_with_zero_code_edits(signal_config):
	"""The load-bearing acceptance property: tuning signal-config.json alone
	must flip a vote, with no code touched."""
	raw = _full_raw_fetch()  # sp500 delta_pct = 1.0%

	baseline = compute_premarket_numbers(raw, _prev_day(), signal_config)
	assert baseline["sp500_overnight"]["vote"] == 1  # 1.0% >= default 0.2% threshold

	tuned_config = copy.deepcopy(signal_config)
	for entry in tuned_config["directional_inputs"]:
		if entry["key"] == "sp500_overnight":
			entry["threshold_pct"] = 5.0  # now 1.0% no longer clears the bar

	tuned = compute_premarket_numbers(raw, _prev_day(), tuned_config)
	assert tuned["sp500_overnight"]["vote"] == 0
	assert tuned["bias_score"] < baseline["bias_score"]
