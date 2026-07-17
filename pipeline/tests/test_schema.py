"""Six deliberately malformed sidecar JSONs — each must fail schema
validation with a clear error (PHASES.md Phase 2 acceptance)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from pipeline.validate.schema import parse_sidecar

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "data" / "days"


@pytest.fixture
def valid_trading_day() -> dict:
	return json.loads((FIXTURES_DIR / "2026-07-09.json").read_text())


@pytest.fixture
def valid_holiday() -> dict:
	return json.loads((FIXTURES_DIR / "2026-01-26.json").read_text())


def test_missing_date_fails(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	del bad["date"]
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_news_item_without_source_url_fails(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	del bad["premarket"]["news"][0]["source_url"]
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_wrong_type_value_fails(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	bad["type"] = "midweek-special"
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_eod_present_before_eod_written_fails(valid_trading_day):
	# CLAUDE.md rule 2: eod must not exist until eod_written flips true.
	bad = copy.deepcopy(valid_trading_day)
	bad["eod_written"] = False
	assert bad["eod"] is not None
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_missing_list_mismatched_with_unavailable_votes_fails(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	bad["missing"] = ["dxy"]  # dxy isn't actually marked unavailable in this fixture
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_holiday_without_reason_fails(valid_holiday):
	bad = copy.deepcopy(valid_holiday)
	del bad["reason"]
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_invalid_source_url_fails(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	bad["premarket"]["news"][0]["source_url"] = "not a real url"
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


def test_suppressed_signal_requires_bias_label_and_score_both_null(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	bad["premarket"]["bias_label"] = None  # score still set -> inconsistent
	with pytest.raises(ValidationError):
		parse_sidecar(bad)


# Outage-page rules (ORCHESTRATION §4 recovery decision, 2026-07-17): empty
# news is legal only on an outage page, and eod_missed is a pre-EOD-only flag.


def test_empty_news_fails_on_a_normal_trading_day(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	bad["premarket"]["news"] = []
	with pytest.raises(ValidationError, match="outage"):
		parse_sidecar(bad)


def test_outage_trading_day_with_empty_news_is_valid():
	raw = json.loads((FIXTURES_DIR / "2026-07-10.json").read_text())
	parsed = parse_sidecar(raw)
	assert parsed.data_quality == "outage"
	assert parsed.premarket.news == []
	assert parsed.eod_missed is True


def test_empty_news_fails_on_a_normal_weekend(valid_holiday):
	bad = copy.deepcopy(valid_holiday)
	bad["news"] = []
	with pytest.raises(ValidationError, match="outage"):
		parse_sidecar(bad)


def test_outage_weekend_with_empty_news_is_valid():
	parsed = parse_sidecar(json.loads((FIXTURES_DIR / "2026-07-12.json").read_text()))
	assert parsed.outage is True
	assert parsed.news == []


def test_eod_missed_after_eod_written_fails(valid_trading_day):
	bad = copy.deepcopy(valid_trading_day)
	assert bad["eod_written"] is True
	bad["eod_missed"] = True
	with pytest.raises(ValidationError, match="eod_missed"):
		parse_sidecar(bad)
