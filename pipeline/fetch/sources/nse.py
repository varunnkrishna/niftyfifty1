"""NSE unofficial JSON API client (ORCHESTRATION §5a primary for India VIX
and FII/DII net cash). NSE's endpoints reject requests with no prior
cookies — a session must first visit the homepage to pick up the
anti-bot cookie before the `/api/*` endpoints will respond.

Note (discovered during Phase 3 implementation): nseindia.com was
completely unreachable (connection-level timeout) from this sandbox's
network — not a bot-detection response, no response at all. This module
could not be live-verified here. The request shape below (session
bootstrap, `Referer` header, the two endpoints) follows NSE's
well-established unofficial API pattern; it should be smoke-tested for
real once this runs somewhere with unrestricted network access (a GitHub
Actions runner, per ORCHESTRATION §1). Every NSE metric already has a
Moneycontrol fallback for exactly this kind of failure (ORCHESTRATION §5a).
"""

from __future__ import annotations

from pipeline.fetch.sources.http import DEFAULT_TIMEOUT, new_session

HOME_URL = "https://www.nseindia.com/"
ALL_INDICES_URL = "https://www.nseindia.com/api/allIndices"
FII_DII_URL = "https://www.nseindia.com/api/fiidiiTradeReact"


def _bootstrapped_session(timeout: int):
	session = new_session()
	session.headers.update({"Accept": "application/json", "Referer": HOME_URL})
	session.get(HOME_URL, timeout=timeout)  # picks up NSE's anti-bot cookies
	return session


def fetch_india_vix(timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"value": level, "delta": change}."""
	session = _bootstrapped_session(timeout)
	resp = session.get(ALL_INDICES_URL, timeout=timeout)
	resp.raise_for_status()
	data = resp.json()

	for row in data.get("data", []):
		if row.get("index", "").upper() == "INDIA VIX":
			return {"value": float(row["last"]), "delta": float(row["variation"])}

	raise ValueError("India VIX not present in NSE allIndices response")


def fetch_fii_dii_net(timeout: int = DEFAULT_TIMEOUT) -> dict:
	"""Returns {"fii_net_cash": ₹cr, "dii_net_cash": ₹cr, "date": ...} for the
	most recent published (T-1) provisional cash-segment figures."""
	session = _bootstrapped_session(timeout)
	resp = session.get(FII_DII_URL, timeout=timeout)
	resp.raise_for_status()
	rows = resp.json()

	latest_date = max(row["date"] for row in rows)
	by_category = {row["category"]: row for row in rows if row["date"] == latest_date}

	fii = by_category.get("FII/FPI") or by_category.get("FII")
	dii = by_category.get("DII")
	if not fii or not dii:
		raise ValueError(f"NSE fiidiiTradeReact missing FII or DII row for {latest_date}")

	return {
		"fii_net_cash": float(fii["buyValue"]) - float(fii["sellValue"]),
		"dii_net_cash": float(dii["buyValue"]) - float(dii["sellValue"]),
		"date": latest_date,
	}
