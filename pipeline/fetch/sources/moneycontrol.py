"""Moneycontrol HTML scraping client (ORCHESTRATION §5a fallback for GIFT
Nifty, FII/DII net cash, India VIX).

Note (discovered during Phase 3 implementation): moneycontrol.com's pages
render fine in a real browser (verified manually — India VIX page confirmed
live at the URL below, current price in a `.pcstkspr` element) but reject
plain `requests`/`curl` HTTP calls with 403, evidently via TLS/JS
fingerprinting rather than a simple User-Agent check. This is a more
fundamental blocker than NSE's flakiness: no amount of header-tuning fixed
it in this sandbox. This client is implemented against the real, verified
page structure and will work the moment the 403 is cleared (e.g. a
residential/datacenter IP with a better bot-reputation, or a headless-
browser-based fetch instead of plain HTTP) — but as committed, expect it to
raise and fall through to the missing-marker path. Flagged to Varun rather
than silently worked around with a heavier dependency (e.g. Playwright).
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

from pipeline.fetch.sources.http import DEFAULT_TIMEOUT, new_session

INDIA_VIX_URL = "https://www.moneycontrol.com/indian-indices/india-vix-36.html"

_NUMBER_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def _parse_price(html: str) -> float:
	soup = BeautifulSoup(html, "html.parser")
	el = soup.select_one(".pcstkspr")
	if el is None:
		raise ValueError("Moneycontrol page structure changed: .pcstkspr not found")
	match = _NUMBER_RE.search(el.get_text(strip=True))
	if not match:
		raise ValueError(f"Could not parse a number from Moneycontrol price element: {el.get_text()!r}")
	return float(match.group().replace(",", ""))


def fetch_india_vix(timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"value": level}. No delta — Moneycontrol's change badge
	selector wasn't confidently identifiable; compute delta from the
	previous day's stored sidecar JSON instead if this path is hit."""
	session = new_session()
	resp = session.get(INDIA_VIX_URL, timeout=timeout)
	resp.raise_for_status()
	return {"value": _parse_price(resp.text)}
