"""Weekend/holiday run entrypoint (ORCHESTRATION §4, ~11:00 IST, daily).
One write: RSS -> reworded news -> assemble -> validate -> publish. No
metrics, no signal (PLANNING §2).
"""

from __future__ import annotations

import sys
from datetime import date

from pipeline.assemble.assembler import assemble_mdx, content_path
from pipeline.compose.client import ComposeError
from pipeline.compose.compose import compose_with_retry
from pipeline.compose.passthrough import PassthroughError, reconstruct_news_items
from pipeline.compose.prompts import build_news_only_prompt
from pipeline.compose.validate_prose import validate_news_item
from pipeline.fetch.rss import fetch_all_feeds
from pipeline.orchestrate.alert import send_alert
from pipeline.orchestrate.common import REPO_ROOT, git_pull, load_day_sidecar, select_news_items, today_ist, write_json
from pipeline.orchestrate.postdeploy import ping_indexnow, verify_live
from pipeline.orchestrate.publish import commit_and_push
from pipeline.orchestrate.resolve import ResolverError, resolve
from pipeline.validate.schema import parse_sidecar

NEWS_ITEM_LIMIT = 8


def _compose_weekend_news(news_items: list[dict]) -> list[dict]:
	system_prompt, user_prompt = build_news_only_prompt(news_items)
	parsed = compose_with_retry(system_prompt, user_prompt)

	if "news" not in parsed:
		raise ComposeError(f"LLM JSON missing 'news' key, got {list(parsed.keys())}")
	try:
		reconstructed = reconstruct_news_items(parsed["news"], news_items)
	except (PassthroughError, KeyError) as exc:
		raise ComposeError(f"LLM news output could not be reconciled with input items: {exc}") from exc

	titles_by_index = {item["index"]: item["title"] for item in news_items}
	violations: list[str] = []
	for entry, reconstructed_item in zip(parsed["news"], reconstructed):
		# No computed numbers exist on a weekend/holiday page — any number
		# in the prose is by definition invented.
		violations += validate_news_item(reconstructed_item, titles_by_index.get(entry.get("index"), ""), known_numbers=set())
	if violations:
		raise ComposeError("COMPOSE validation gate failed:\n" + "\n".join(violations))

	return reconstructed


def run(iso_date: str) -> int:
	git_pull()

	try:
		day_type, reason = resolve(date.fromisoformat(iso_date))
	except ResolverError as exc:
		send_alert("high", f"News run failed: {exc}")
		return 1

	if day_type == "trading":
		print(f"{iso_date} is a trading day — news run is a no-op (handled by premarket/eod).")
		return 0

	if load_day_sidecar(iso_date) is not None:
		print(f"{iso_date} already published — idempotent no-op.")
		return 0

	try:
		rss = fetch_all_feeds()
		news_items = select_news_items([vars(item) for item in rss.items], NEWS_ITEM_LIMIT)
		composed_news = _compose_weekend_news(news_items)

		sidecar = {"date": iso_date, "type": day_type, "news": composed_news}
		if day_type == "holiday":
			sidecar["reason"] = reason
		parse_sidecar(sidecar)  # raises -> nothing written, nothing committed

		sidecar_path = REPO_ROOT / "data" / "days" / f"{iso_date}.json"
		write_json(sidecar_path, sidecar)

		mdx_path = REPO_ROOT / content_path(iso_date)
		mdx_path.parent.mkdir(parents=True, exist_ok=True)
		mdx_path.write_text(assemble_mdx(sidecar))

		committed = commit_and_push([sidecar_path, mdx_path], f"news {iso_date}")
		if committed and verify_live(iso_date):
			ping_indexnow(iso_date)

		return 0
	except Exception as exc:  # noqa: BLE001 - top-level run boundary
		message = f"News run failed for {iso_date} at some stage: {exc}"
		print(f"[run] news {iso_date}: FAILED — {message}", flush=True)
		send_alert("high", message)
		return 1


if __name__ == "__main__":
	raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1 else run(today_ist().isoformat()))
