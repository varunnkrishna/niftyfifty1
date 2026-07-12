"""FRED CSV client (ORCHESTRATION §5a primary for US 10Y yield). Uses the
public fredgraph.csv download, which needs no API key — the only source in
§5a's table that doesn't (ORCHESTRATION §9's secrets list has no FRED key).
"""

from __future__ import annotations

import csv
import io

import requests

from pipeline.fetch.sources.http import DEFAULT_TIMEOUT

BASE_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def fetch_series_latest(series_id: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"value": latest level, "delta": vs previous observation, "date": ...}.

	Deliberately does NOT use the shared browser-spoofing session (http.py) —
	this plain government CSV endpoint has been observed rejecting/hanging on
	requests carrying a desktop-browser User-Agent while accepting the
	default `python-requests` one; the reverse of every other source here.
	"""
	resp = requests.get(BASE_URL, params={"id": series_id}, timeout=timeout)
	resp.raise_for_status()

	reader = csv.reader(io.StringIO(resp.text))
	rows = [row for row in reader if row and row[0] != "DATE" and len(row) == 2 and row[1] not in (".", "")]
	if len(rows) < 2:
		raise ValueError(f"FRED series {series_id} did not return enough observations")

	(prev_date, prev_val), (latest_date, latest_val) = rows[-2], rows[-1]
	latest = float(latest_val)
	prev = float(prev_val)
	return {"value": latest, "delta": latest - prev, "date": latest_date}
