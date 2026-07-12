"""EOD index closes (ORCHESTRATION §5a "Index closes / breadth / sectors —
EOD run only"). Discovered gap: Phase 3 only built the 11 pre-market
fetchers; this was missing until Phase 7 needed it for the EOD orchestration
script.

Uses Yahoo Finance uniformly for all three indices rather than the source
table's literal "NSE primary" — Sensex is a *BSE* index, not NSE, so an
NSE-only primary can't actually serve it; Yahoo covers all three (`^NSEI`,
`^NSEBANK`, `^BSESN`) consistently and was already verified live and
reliable in Phase 3. NSE's own `allIndices` (nifty/banknifty only, no
Sensex) is the fallback for the two it can serve.

Market breadth (advance/decline) and sector leaders/laggards are NOT
fetched here — no verified working source was found (Moneycontrol pages
403 to plain HTTP, same as discovered in Phase 3). These stay optional in
the schema and are simply omitted rather than guessed at (CLAUDE.md rule 4).
"""

from __future__ import annotations

from pipeline.fetch.retry import DEFAULT_BACKOFFS_SECONDS, FetchOutcome, fetch_with_fallback
from pipeline.fetch.sources import nse, yahoo

_NSE_INDEX_NAMES = {"nifty_close": "NIFTY 50", "banknifty_close": "NIFTY BANK"}


def fetch_eod_close(key: str, yahoo_symbol: str, **kw) -> FetchOutcome:
	fallback = None
	if key in _NSE_INDEX_NAMES:
		fallback = ("nse", lambda: nse.fetch_index(_NSE_INDEX_NAMES[key]))

	return fetch_with_fallback(
		key,
		primary=("yahoo", lambda: yahoo.fetch_quote(yahoo_symbol)),
		fallback=fallback,
		**kw,
	)


def fetch_all_eod_closes(backoffs=DEFAULT_BACKOFFS_SECONDS, sleep_fn=None) -> dict[str, FetchOutcome]:
	import time as _time

	sleep_fn = sleep_fn or _time.sleep
	kw = {"backoffs": backoffs, "sleep_fn": sleep_fn}
	return {
		"nifty_close": fetch_eod_close("nifty_close", "^NSEI", **kw),
		"sensex_close": fetch_eod_close("sensex_close", "^BSESN", **kw),
		"banknifty_close": fetch_eod_close("banknifty_close", "^NSEBANK", **kw),
	}
