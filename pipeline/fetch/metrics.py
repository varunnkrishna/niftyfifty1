"""Per-metric fetchers wired to their primary/fallback sources exactly per
ORCHESTRATION §5a's table. Each returns a `FetchOutcome` — never raises;
a metric that exhausts every source becomes `unavailable`, which the
compute layer (Phase 4) turns into vote=0 / degraded-data notices per the
ORCHESTRATION §5b ladder.

Two gaps discovered during implementation, deliberately left unfallback'd
rather than guessed at (CLAUDE.md: never invent a value to fill a gap):
GIFT Nifty and FII/DII net cash have no confidently-identified Moneycontrol
URL (every guess 403'd through plain HTTP — see sources/moneycontrol.py).
If NSE/Yahoo fail for these, they go straight to `unavailable`.
"""

from __future__ import annotations

from pipeline.fetch.retry import DEFAULT_BACKOFFS_SECONDS, FetchOutcome, fetch_with_fallback
from pipeline.fetch.sources import fred, moneycontrol, nse, stooq, yahoo

DIRECTIONAL_METRICS = (
	"gift_nifty",
	"sp500_overnight",
	"nasdaq_overnight",
	"us10y_yield",
	"dxy",
	"fii_net_cash",
	"dii_net_cash",
	"usdinr",
	"prev_close_in_range",
)
CONTEXT_METRICS = ("india_vix", "brent")
ALL_METRICS = DIRECTIONAL_METRICS + CONTEXT_METRICS


def fetch_gift_nifty(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"gift_nifty",
		primary=("yahoo", lambda: yahoo.fetch_quote("GIFTNIFTY.NS")),
		fallback=None,  # see module docstring
		**kw,
	)


def fetch_sp500_overnight(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"sp500_overnight",
		primary=("yahoo", lambda: yahoo.fetch_quote("^GSPC")),
		fallback=("stooq", lambda: stooq.fetch_quote("^spx")),
		**kw,
	)


def fetch_nasdaq_overnight(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"nasdaq_overnight",
		primary=("yahoo", lambda: yahoo.fetch_quote("^IXIC")),
		fallback=("stooq", lambda: stooq.fetch_quote("^ndq")),
		**kw,
	)


def fetch_us10y_yield(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"us10y_yield",
		primary=("fred", lambda: fred.fetch_series_latest("DGS10")),
		fallback=("yahoo", lambda: yahoo.fetch_quote("^TNX")),
		**kw,
	)


def fetch_dxy(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"dxy",
		primary=("yahoo", lambda: yahoo.fetch_quote("DX-Y.NYB")),
		fallback=("stooq", lambda: stooq.fetch_quote("dx.f")),
		**kw,
	)


def fetch_brent(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"brent",
		primary=("yahoo", lambda: yahoo.fetch_quote("BZ=F")),
		fallback=None,  # ORCHESTRATION §5a: context note only, no fallback listed
		**kw,
	)


def fetch_usdinr(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"usdinr",
		primary=("yahoo", lambda: yahoo.fetch_quote("INR=X")),
		fallback=None,  # ORCHESTRATION §5a: no fallback listed
		**kw,
	)


def fetch_india_vix(**kw) -> FetchOutcome:
	return fetch_with_fallback(
		"india_vix",
		primary=("nse", lambda: nse.fetch_india_vix()),
		fallback=("moneycontrol", lambda: moneycontrol.fetch_india_vix()),
		**kw,
	)


def fetch_fii_dii(**kw) -> FetchOutcome:
	"""NSE returns FII and DII net cash in one call; exposed as a single
	combined outcome (value is a dict of both) and split by the caller."""
	return fetch_with_fallback(
		"fii_dii",
		primary=("nse", lambda: nse.fetch_fii_dii_net()),
		fallback=None,  # see module docstring
		**kw,
	)


def _classify_range(close: float, low: float, high: float) -> str:
	span = high - low
	if span <= 0:
		return "middle third"
	position = (close - low) / span
	if position >= 2 / 3:
		return "top third"
	if position <= 1 / 3:
		return "bottom third"
	return "middle third"


def fetch_prev_close_in_range(prev_day_sidecar: dict | None, nse_symbol: str = "^NSEI", **kw) -> FetchOutcome:
	"""Primary: the prior day's own stored sidecar JSON (ORCHESTRATION §5a —
	"this is why the sidecar archive pays off immediately"). The sidecar
	schema doesn't yet persist day_low/day_high (a Phase 4 schema
	extension), so this will usually fall through to the Yahoo OHLC
	fallback today — by design, not a bug."""

	def from_archive():
		if not prev_day_sidecar:
			raise ValueError("no prior day sidecar JSON available")
		eod = prev_day_sidecar.get("eod")
		if not eod or "day_low" not in eod or "day_high" not in eod:
			raise ValueError("prior day sidecar JSON has no stored day range yet")
		return _classify_range(eod["nifty_close"]["value"], eod["day_low"], eod["day_high"])

	def from_yahoo():
		r = yahoo.fetch_day_range(nse_symbol)
		return _classify_range(r["close"], r["low"], r["high"])

	return fetch_with_fallback(
		"prev_close_in_range",
		primary=("archive", from_archive),
		fallback=("yahoo_ohlc", from_yahoo),
		**kw,
	)


def fetch_all_metrics(prev_day_sidecar: dict | None = None, backoffs=DEFAULT_BACKOFFS_SECONDS, sleep_fn=None) -> dict[str, FetchOutcome]:
	import time as _time

	sleep_fn = sleep_fn or _time.sleep
	kw = {"backoffs": backoffs, "sleep_fn": sleep_fn}

	outcomes: dict[str, FetchOutcome] = {
		"gift_nifty": fetch_gift_nifty(**kw),
		"sp500_overnight": fetch_sp500_overnight(**kw),
		"nasdaq_overnight": fetch_nasdaq_overnight(**kw),
		"us10y_yield": fetch_us10y_yield(**kw),
		"dxy": fetch_dxy(**kw),
		"brent": fetch_brent(**kw),
		"usdinr": fetch_usdinr(**kw),
		"india_vix": fetch_india_vix(**kw),
		"prev_close_in_range": fetch_prev_close_in_range(prev_day_sidecar, **kw),
	}

	fii_dii = fetch_fii_dii(**kw)
	if fii_dii.unavailable:
		outcomes["fii_net_cash"] = FetchOutcome("fii_net_cash", None, None, True, fii_dii.errors)
		outcomes["dii_net_cash"] = FetchOutcome("dii_net_cash", None, None, True, fii_dii.errors)
	else:
		outcomes["fii_net_cash"] = FetchOutcome("fii_net_cash", fii_dii.value["fii_net_cash"], fii_dii.source, False, fii_dii.errors)
		outcomes["dii_net_cash"] = FetchOutcome("dii_net_cash", fii_dii.value["dii_net_cash"], fii_dii.source, False, fii_dii.errors)

	return outcomes
