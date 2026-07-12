"""EOD run entrypoint (ORCHESTRATION §4, ~16:20 IST, trading days).

Reads the day's already-committed sidecar JSON (written by the pre-market
run) and merges in the `eod` block — never touching a single key inside
`premarket` (CLAUDE.md rule 2). The immutability is structural: this script
only ever adds an `eod` key and flips `eod_written`; it has no code path
that writes into `premarket` at all.
"""

from __future__ import annotations

import sys
from datetime import date

from pipeline.assemble.assembler import assemble_mdx, content_path
from pipeline.compose.compose import compose_eod
from pipeline.compose.setup_summary import render_eod_summary
from pipeline.fetch.eod_metrics import fetch_all_eod_closes
from pipeline.fetch.rss import fetch_all_feeds
from pipeline.orchestrate.alert import send_alert
from pipeline.orchestrate.common import REPO_ROOT, git_pull, load_day_sidecar, select_news_items, today_ist, write_json
from pipeline.orchestrate.postdeploy import ping_indexnow, verify_live
from pipeline.orchestrate.publish import commit_and_push
from pipeline.orchestrate.resolve import ResolverError, resolve
from pipeline.validate.schema import parse_sidecar

NEWS_ITEM_LIMIT = 10


def run(iso_date: str) -> int:
	git_pull()

	try:
		day_type, _ = resolve(date.fromisoformat(iso_date))
	except ResolverError as exc:
		send_alert("high", f"EOD run failed: {exc}")
		return 1

	if day_type != "trading":
		print(f"{iso_date} is a {day_type} day — EOD run is a no-op.")
		return 0

	sidecar = load_day_sidecar(iso_date)
	if sidecar is None or not sidecar.get("premarket"):
		send_alert("high", f"EOD run for {iso_date} found no pre-market entry to append to.")
		return 1

	if sidecar.get("eod_written"):
		print(f"EOD for {iso_date} already published — idempotent no-op.")
		return 0

	try:
		close_outcomes = fetch_all_eod_closes()
		missing_closes = [k for k, v in close_outcomes.items() if v.unavailable]
		if missing_closes:
			raise RuntimeError(f"EOD close fetch failed for: {missing_closes}")

		eod_numbers = {
			key: {"value": outcome.value["value"], "delta_pct": outcome.value["delta_pct"]}
			for key, outcome in close_outcomes.items()
		}

		rss = fetch_all_feeds()
		news_items = select_news_items([vars(item) for item in rss.items], NEWS_ITEM_LIMIT)
		setup_summary = render_eod_summary(eod_numbers)
		composed = compose_eod(news_items, eod_numbers, setup_summary)

		# The only mutation: add `eod`, flip `eod_written`. `premarket` is
		# copied through byte-for-byte from the loaded sidecar, untouched.
		updated_sidecar = {
			**sidecar,
			"eod_written": True,
			"eod": {**eod_numbers, **composed},
		}
		parse_sidecar(updated_sidecar)  # raises -> nothing written, nothing committed

		sidecar_path = REPO_ROOT / "data" / "days" / f"{iso_date}.json"
		write_json(sidecar_path, updated_sidecar)

		mdx_path = REPO_ROOT / content_path(iso_date)
		mdx_path.write_text(assemble_mdx(updated_sidecar))

		committed = commit_and_push([sidecar_path, mdx_path], f"eod {iso_date}")
		if committed and verify_live(iso_date, expect_eod=True):
			ping_indexnow(iso_date)

		return 0
	except Exception as exc:  # noqa: BLE001 - top-level run boundary
		send_alert("high", f"EOD run failed for {iso_date} at some stage: {exc}")
		return 1


if __name__ == "__main__":
	raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1 else run(today_ist().isoformat()))
