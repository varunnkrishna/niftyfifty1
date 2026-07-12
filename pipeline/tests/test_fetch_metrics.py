"""Metric-level wiring: each metric's primary/fallback pairing actually
matches ORCHESTRATION §5a, verified with the network mocked out."""

from __future__ import annotations

from unittest.mock import patch

from pipeline.fetch import metrics


def _no_sleep(_seconds: float) -> None:
	pass


def test_sp500_falls_back_to_stooq_when_yahoo_fails():
	with (
		patch("pipeline.fetch.metrics.yahoo.fetch_quote", side_effect=ConnectionError("blocked")),
		patch("pipeline.fetch.metrics.stooq.fetch_quote", return_value={"value": 7500.0, "open": 7480.0}),
	):
		outcome = metrics.fetch_sp500_overnight(backoffs=(0, 0), sleep_fn=_no_sleep)

	assert outcome.source == "stooq"
	assert outcome.value == {"value": 7500.0, "open": 7480.0}


def test_india_vix_falls_back_to_moneycontrol_when_nse_fails():
	with (
		patch("pipeline.fetch.metrics.nse.fetch_india_vix", side_effect=TimeoutError("nse down")),
		patch("pipeline.fetch.metrics.moneycontrol.fetch_india_vix", return_value={"value": 13.1}),
	):
		outcome = metrics.fetch_india_vix(backoffs=(0, 0), sleep_fn=_no_sleep)

	assert outcome.source == "moneycontrol"
	assert outcome.value == {"value": 13.1}


def test_gift_nifty_has_no_fallback_goes_straight_to_missing():
	with patch("pipeline.fetch.metrics.yahoo.fetch_quote", side_effect=ValueError("no symbol")):
		outcome = metrics.fetch_gift_nifty(backoffs=(0, 0), sleep_fn=_no_sleep)

	assert outcome.unavailable is True
	assert outcome.source is None


def test_prev_close_in_range_uses_archive_when_present():
	prev_day = {
		"eod": {
			"nifty_close": {"value": 24500},
			"day_low": 24300,
			"day_high": 24600,
		}
	}
	with patch("pipeline.fetch.metrics.yahoo.fetch_day_range") as mock_yahoo:
		outcome = metrics.fetch_prev_close_in_range(prev_day, backoffs=(0, 0), sleep_fn=_no_sleep)

	assert outcome.source == "archive"
	assert outcome.value == "top third"  # (24500-24300)/(24600-24300) = 0.667
	mock_yahoo.assert_not_called()


def test_prev_close_in_range_falls_back_to_yahoo_when_archive_missing():
	with patch("pipeline.fetch.metrics.yahoo.fetch_day_range", return_value={"close": 100, "low": 90, "high": 110}):
		outcome = metrics.fetch_prev_close_in_range(prev_day_sidecar=None, backoffs=(0, 0), sleep_fn=_no_sleep)

	assert outcome.source == "yahoo_ohlc"
	assert outcome.value == "middle third"


def test_fetch_all_metrics_splits_combined_fii_dii_outcome():
	with patch(
		"pipeline.fetch.metrics.nse.fetch_fii_dii_net",
		return_value={"fii_net_cash": -1200.0, "dii_net_cash": 800.0, "date": "2026-07-10"},
	):
		with patch("pipeline.fetch.metrics.fetch_gift_nifty") as m1, \
			patch("pipeline.fetch.metrics.fetch_sp500_overnight") as m2, \
			patch("pipeline.fetch.metrics.fetch_nasdaq_overnight") as m3, \
			patch("pipeline.fetch.metrics.fetch_us10y_yield") as m4, \
			patch("pipeline.fetch.metrics.fetch_dxy") as m5, \
			patch("pipeline.fetch.metrics.fetch_brent") as m6, \
			patch("pipeline.fetch.metrics.fetch_usdinr") as m7, \
			patch("pipeline.fetch.metrics.fetch_india_vix") as m8, \
			patch("pipeline.fetch.metrics.fetch_prev_close_in_range") as m9:
			for m in (m1, m2, m3, m4, m5, m6, m7, m8, m9):
				m.return_value = metrics.FetchOutcome("x", 1, "stub", False, [])

			outcomes = metrics.fetch_all_metrics(prev_day_sidecar=None, backoffs=(0, 0), sleep_fn=_no_sleep)

	assert outcomes["fii_net_cash"].value == -1200.0
	assert outcomes["dii_net_cash"].value == 800.0
	assert outcomes["fii_net_cash"].source == "nse"
