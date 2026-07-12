"""Stooq CSV client (ORCHESTRATION §5a fallback for S&P 500, Nasdaq, DXY).

Note (discovered during Phase 3 implementation): Stooq's `/q/l/` CSV
endpoint now sits behind a JavaScript proof-of-work challenge and no longer
returns CSV to a plain HTTP client. This module is implemented per spec —
correct request shape, correct parsing — but should be expected to raise
and fall through to the missing-marker path until/unless Stooq's endpoint
is reachable again. The retry/fallback/missing design (ORCHESTRATION §5b)
exists precisely to tolerate exactly this kind of source failure.
"""

from __future__ import annotations

import csv
import io

from pipeline.fetch.sources.http import DEFAULT_TIMEOUT, new_session

BASE_URL = "https://stooq.com/q/l/"


def fetch_quote(symbol: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"value": close, "open": open}."""
	session = new_session()
	resp = session.get(BASE_URL, params={"s": symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"}, timeout=timeout)
	resp.raise_for_status()

	reader = csv.DictReader(io.StringIO(resp.text))
	row = next(reader, None)
	if row is None or row.get("Close") in (None, "", "N/D"):
		raise ValueError(f"Stooq returned no usable data for {symbol}")

	return {"value": float(row["Close"]), "open": float(row["Open"])}
