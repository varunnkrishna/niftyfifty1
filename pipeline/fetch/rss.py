"""RSS layer for the four news feeds (PLANNING §6, ORCHESTRATION §5a).
A dead feed is a warning, not a failure — news selection works from
whatever feeds responded, minimum one (ORCHESTRATION §5a).

Note (discovered during Phase 3 implementation): Business Standard's RSS
endpoint returns 403 to every plain-HTTP client tried here (curl,
feedparser's own fetcher, and a browser-UA `requests` session alike) — a
real, confirmed block, not a guessed-wrong URL. This is exactly the
scenario the "dead feed is a warning" design tolerates: the other three
feeds (Moneycontrol, ET Markets, Livemint) were all verified live and
working.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import datetime, timezone

import feedparser
import requests

from pipeline.fetch.sources.http import DEFAULT_TIMEOUT

FEEDS = {
	"Moneycontrol": "https://www.moneycontrol.com/rss/marketreports.xml",
	"ET Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
	"Livemint": "https://www.livemint.com/rss/markets",
	"Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
}


@dataclass
class RssItem:
	source_name: str
	title: str
	link: str
	published: str


@dataclass
class RssFetchResult:
	items: list[RssItem]
	warnings: list[str] = field(default_factory=list)


def _to_iso8601(entry: dict) -> str:
	# feedparser normalizes published/updated into a UTC struct_time when it
	# can parse the feed's native format (RFC 822 in practice, for these
	# feeds) — converting that rather than passing the raw string through is
	# what makes the timestamp satisfy the sidecar schema's ISO 8601 check.
	parsed = entry.get("published_parsed") or entry.get("updated_parsed")
	if parsed:
		return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc).isoformat()
	return entry.get("published", entry.get("updated", ""))


def fetch_feed(source_name: str, url: str, timeout: int = DEFAULT_TIMEOUT) -> list[RssItem]:
	# Deliberately NOT the shared browser-spoofing session (sources/http.py) —
	# observed live (Phase 3): Moneycontrol's RSS accepts the default
	# `python-requests` UA but 403s a desktop-Chrome UA. Same inversion as
	# FRED (sources/fred.py) — different sites, opposite bot-detection logic.
	resp = requests.get(url, timeout=timeout)
	resp.raise_for_status()

	parsed = feedparser.parse(resp.content)
	if parsed.bozo and not parsed.entries:
		raise ValueError(f"{source_name} feed did not parse: {parsed.bozo_exception}")

	return [
		RssItem(
			source_name=source_name,
			title=entry.get("title", "").strip(),
			link=entry.get("link", ""),
			published=_to_iso8601(entry),
		)
		for entry in parsed.entries
		if entry.get("title") and entry.get("link")
	]


def fetch_all_feeds(feeds: dict[str, str] = FEEDS) -> RssFetchResult:
	items: list[RssItem] = []
	warnings: list[str] = []

	for source_name, url in feeds.items():
		try:
			items.extend(fetch_feed(source_name, url))
		except Exception as exc:  # noqa: BLE001 - a dead feed is a warning, not fatal
			warnings.append(f"{source_name} feed failed: {exc}")

	if not items:
		raise RuntimeError("all RSS feeds failed — news selection needs at least one working feed")

	return RssFetchResult(items=items, warnings=warnings)
