"""Builds the raw-fetch JSON (PHASES.md Phase 3): value + source-used +
missing[] per metric, plus whatever RSS items came through. This is a
pipeline-internal intermediate consumed by COMPUTE (Phase 4) — not the
sidecar JSON (data/days/*.json), which is the permanent, committed source
of truth assembled later in the pipeline (ORCHESTRATION §3).
"""

from __future__ import annotations

from datetime import datetime, timezone

from pipeline.fetch.metrics import ALL_METRICS, fetch_all_metrics
from pipeline.fetch.retry import DEFAULT_BACKOFFS_SECONDS, FetchOutcome
from pipeline.fetch.rss import RssItem, fetch_all_feeds


def _outcome_to_dict(outcome: FetchOutcome) -> dict:
	return {
		"value": outcome.value,
		"source": outcome.source,
		"unavailable": outcome.unavailable,
	}


def _news_item_to_dict(item: RssItem) -> dict:
	return {
		"source_name": item.source_name,
		"title": item.title,
		"link": item.link,
		"published": item.published,
	}


def build_raw_fetch(iso_date: str, prev_day_sidecar: dict | None, backoffs=DEFAULT_BACKOFFS_SECONDS, sleep_fn=None) -> dict:
	print(f"[fetch] starting metrics fetch for {iso_date}...", flush=True)
	metric_outcomes = fetch_all_metrics(prev_day_sidecar=prev_day_sidecar, backoffs=backoffs, sleep_fn=sleep_fn)
	missing = sorted(name for name, outcome in metric_outcomes.items() if outcome.unavailable)
	print(f"[fetch] metrics fetch done — {len(missing)} missing: {missing}", flush=True)

	rss_warnings: list[str] = []
	news_items: list[dict] = []
	print("[fetch] starting RSS fetch...", flush=True)
	try:
		rss_result = fetch_all_feeds()
		news_items = [_news_item_to_dict(item) for item in rss_result.items]
		rss_warnings = rss_result.warnings
		print(f"[fetch] RSS fetch done — {len(news_items)} items, {len(rss_warnings)} feed warnings", flush=True)
	except RuntimeError as exc:
		rss_warnings = [str(exc)]
		print(f"[fetch] RSS fetch failed entirely: {exc}", flush=True)

	return {
		"date": iso_date,
		"fetched_at": datetime.now(timezone.utc).isoformat(),
		"metrics": {name: _outcome_to_dict(metric_outcomes[name]) for name in ALL_METRICS},
		"missing": missing,
		"news": news_items,
		"rss_warnings": rss_warnings,
	}
