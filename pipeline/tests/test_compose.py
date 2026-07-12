"""COMPOSE-stage acceptance tests (PHASES.md Phase 5), network fully
mocked: an invented number is caught, a verbatim-copy headline is caught,
and malformed JSON never reaches a commit (retries, then fails cleanly)."""

from __future__ import annotations

import json
from unittest.mock import patch

import pytest

from pipeline.compose.client import ComposeError
from pipeline.compose.compose import compose_premarket

NEWS_ITEMS = [
	{"index": 0, "title": "Sensex gains 300 points as IT stocks rally", "source_name": "Moneycontrol", "source_url": "https://www.moneycontrol.com/x", "timestamp": "2026-07-13T08:00:00+05:30"},
]

PREMARKET_NUMBERS = {
	"gift_nifty": {"vote": 1, "value": 24500, "delta_pct": 0.42},
	"sp500_overnight": {"vote": 0, "value": 5000, "delta_pct": 0.1},
	"bias_score": 2,
	"bias_label": "Long",
	"conviction": "normal",
}


def _mock_response(content: str):
	return content


def test_invented_number_is_caught():
	llm_output = json.dumps(
		{
			"news": [{"index": 0, "headline_reworded": "IT names lead early gains ahead of the open", "why_it_matters": "FII inflows of 9,999 crore drove the rally."}],
			"market_expectations": "Markets look set for a firm start today.",
		}
	)
	with patch("pipeline.compose.compose.call_llm", return_value=llm_output):
		with pytest.raises(ComposeError, match="9999"):
			compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")


def test_verbatim_copy_headline_is_caught():
	llm_output = json.dumps(
		{
			"news": [{"index": 0, "headline_reworded": "Sensex gains 300 points as IT stocks rally", "why_it_matters": "IT strength is lifting the index this morning."}],
			"market_expectations": "Markets look set for a firm start today.",
		}
	)
	with patch("pipeline.compose.compose.call_llm", return_value=llm_output):
		with pytest.raises(ComposeError, match="verbatim copy"):
			compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")


def test_malformed_json_retries_then_fails_cleanly():
	call_count = {"n": 0}

	def always_broken(*args, **kwargs):
		call_count["n"] += 1
		return "this is not JSON at all {{{"

	with patch("pipeline.compose.compose.call_llm", side_effect=always_broken):
		with pytest.raises(ComposeError, match="failed to parse as JSON after 3 attempts"):
			compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")

	assert call_count["n"] == 3  # initial attempt + 2 retries, never more


def test_malformed_json_then_recovers_on_retry():
	responses = iter(["not json", json.dumps({
		"news": [{"index": 0, "headline_reworded": "IT-led gains lift the index ahead of the bell", "why_it_matters": "Tech strength is setting an upbeat tone."}],
		"market_expectations": "Markets look set for a firm start today.",
	})])

	with patch("pipeline.compose.compose.call_llm", side_effect=lambda *a, **k: next(responses)):
		result = compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")

	assert result["news"][0]["source_url"] == "https://www.moneycontrol.com/x"  # passthrough intact
	assert result["market_expectations"] == "Markets look set for a firm start today."


def test_url_in_prose_is_caught():
	llm_output = json.dumps(
		{
			"news": [{"index": 0, "headline_reworded": "IT-led gains lift the index ahead of the bell", "why_it_matters": "See https://example.com for details."}],
			"market_expectations": "Markets look set for a firm start today.",
		}
	)
	with patch("pipeline.compose.compose.call_llm", return_value=llm_output):
		with pytest.raises(ComposeError, match="URL"):
			compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")


def test_unknown_news_index_is_caught():
	llm_output = json.dumps(
		{
			"news": [{"index": 7, "headline_reworded": "IT-led gains lift the index ahead of the bell", "why_it_matters": "Tech strength is setting an upbeat tone."}],
			"market_expectations": "Markets look set for a firm start today.",
		}
	)
	with patch("pipeline.compose.compose.call_llm", return_value=llm_output):
		with pytest.raises(ComposeError, match="index"):
			compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")


def test_valid_composition_passes_and_passthrough_is_exact():
	llm_output = json.dumps(
		{
			"news": [{"index": 0, "headline_reworded": "IT-led gains lift the index ahead of the bell", "why_it_matters": "Tech strength is setting an upbeat tone."}],
			"market_expectations": "Markets look set for a firm start today, tracking overnight strength.",
		}
	)
	with patch("pipeline.compose.compose.call_llm", return_value=llm_output):
		result = compose_premarket(NEWS_ITEMS, PREMARKET_NUMBERS, "setup summary text")

	assert result["news"][0]["headline_reworded"] == "IT-led gains lift the index ahead of the bell"
	assert result["news"][0]["source_name"] == "Moneycontrol"
	assert result["news"][0]["timestamp"] == "2026-07-13T08:00:00+05:30"
