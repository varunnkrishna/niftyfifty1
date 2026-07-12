"""Yahoo Finance quote client (ORCHESTRATION §5a primary for GIFT Nifty,
S&P 500, Nasdaq, DXY, Brent, USD/INR). Public chart-quote endpoint, no key.
"""

from __future__ import annotations

from pipeline.fetch.sources.http import DEFAULT_TIMEOUT, new_session

BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"


def fetch_quote(symbol: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"value": last price/level, "prev_close": ..., "delta_pct": ...}."""
	session = new_session()
	resp = session.get(BASE_URL.format(symbol=symbol), params={"interval": "1d", "range": "5d"}, timeout=timeout)
	resp.raise_for_status()
	payload = resp.json()

	result = payload.get("chart", {}).get("result")
	if not result:
		error = payload.get("chart", {}).get("error")
		raise ValueError(f"Yahoo Finance returned no result for {symbol}: {error}")

	meta = result[0]["meta"]
	price = meta.get("regularMarketPrice")
	prev_close = meta.get("previousClose") or meta.get("chartPreviousClose")
	if price is None:
		raise ValueError(f"Yahoo Finance response for {symbol} missing regularMarketPrice")

	delta_pct = None
	if prev_close:
		delta_pct = (price - prev_close) / prev_close * 100

	return {"value": price, "prev_close": prev_close, "delta_pct": delta_pct}


def fetch_day_range(symbol: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"close": ..., "low": ..., "high": ...} for the current session.
	Used as the fallback source for prev_close_in_range (ORCHESTRATION §5a) —
	the primary source is the prior day's own stored sidecar JSON.
	"""
	session = new_session()
	resp = session.get(BASE_URL.format(symbol=symbol), params={"interval": "1d", "range": "5d"}, timeout=timeout)
	resp.raise_for_status()
	meta = resp.json()["chart"]["result"][0]["meta"]

	close, low, high = meta.get("regularMarketPrice"), meta.get("regularMarketDayLow"), meta.get("regularMarketDayHigh")
	if close is None or low is None or high is None:
		raise ValueError(f"Yahoo Finance response for {symbol} missing day range fields")

	return {"close": close, "low": low, "high": high}
