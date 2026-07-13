"""Pre-market run entrypoint (ORCHESTRATION §4, ~08:40 IST, trading days).

FETCH -> COMPUTE -> COMPOSE -> ASSEMBLE -> VALIDATE -> PUBLISH. Nothing is
written to disk until VALIDATE passes, and nothing is committed until the
write succeeds — so a crash at any earlier stage naturally leaves the repo
untouched (PHASES.md Phase 7 acceptance: "a run killed mid-FETCH... commits
nothing"), no special-case handling required.
"""

from __future__ import annotations

import sys
from datetime import date

from pipeline.assemble.assembler import assemble_mdx, content_path
from pipeline.compose.compose import compose_premarket
from pipeline.compose.setup_summary import render_premarket_summary
from pipeline.compute.engine import compute_premarket_numbers
from pipeline.fetch.raw_output import build_raw_fetch
from pipeline.orchestrate.alert import send_alert
from pipeline.orchestrate.common import (
	REPO_ROOT,
	git_pull,
	load_day_sidecar,
	load_prev_day_sidecar,
	load_signal_config,
	missed_day_check,
	select_news_items,
	today_ist,
	write_json,
)
from pipeline.orchestrate.postdeploy import ping_indexnow, verify_live
from pipeline.orchestrate.publish import commit_and_push
from pipeline.orchestrate.resolve import ResolverError, check_holiday_calendar_expiry, resolve
from pipeline.validate.schema import parse_sidecar

NEWS_ITEM_LIMIT = 5


def run(iso_date: str) -> int:
	today = date.fromisoformat(iso_date)

	git_pull()

	expiry_warning = check_holiday_calendar_expiry(today)
	if expiry_warning:
		send_alert("config", expiry_warning)

	missed_day_check(today)

	try:
		day_type, _ = resolve(today)
	except ResolverError as exc:
		send_alert("high", f"Pre-market run failed: {exc}")
		return 1

	if day_type != "trading":
		print(f"{iso_date} is a {day_type} day — pre-market run is a no-op.")
		return 0

	# Idempotency: already published -> skip re-fetching/recomposing entirely
	# rather than relying on re-running to coincidentally produce identical
	# output (the LLM's COMPOSE call isn't literally deterministic).
	existing = load_day_sidecar(iso_date)
	if existing and existing.get("premarket"):
		print(f"Pre-market for {iso_date} already published — idempotent no-op.")
		return 0

	try:
		print(f"[run] premarket {iso_date}: loading prior context...", flush=True)
		prev_day_sidecar = load_prev_day_sidecar(today)
		signal_config = load_signal_config()

		print(f"[run] premarket {iso_date}: FETCH starting...", flush=True)
		raw = build_raw_fetch(iso_date, prev_day_sidecar)
		print(f"[run] premarket {iso_date}: FETCH done. COMPUTE starting...", flush=True)
		numbers = compute_premarket_numbers(raw, prev_day_sidecar, signal_config)
		print(f"[run] premarket {iso_date}: COMPUTE done (bias_score={numbers.get('bias_score')}). COMPOSE starting...", flush=True)

		news_items = select_news_items(raw["news"], NEWS_ITEM_LIMIT)
		setup_summary = render_premarket_summary(numbers)
		composed = compose_premarket(news_items, numbers, setup_summary)
		print(f"[run] premarket {iso_date}: COMPOSE done. ASSEMBLE/VALIDATE starting...", flush=True)

		data_quality = numbers.pop("data_quality")
		missing = numbers.pop("missing")
		sidecar = {
			"date": iso_date,
			"type": "trading-day",
			"premarket": {**numbers, **composed},
			"data_quality": data_quality,
			"missing": missing,
			"eod_written": False,
		}
		parse_sidecar(sidecar)  # raises -> nothing written, nothing committed
		print(f"[run] premarket {iso_date}: VALIDATE passed. Writing files...", flush=True)

		sidecar_path = REPO_ROOT / "data" / "days" / f"{iso_date}.json"
		write_json(sidecar_path, sidecar)

		mdx_path = REPO_ROOT / content_path(iso_date)
		mdx_path.parent.mkdir(parents=True, exist_ok=True)
		mdx_path.write_text(assemble_mdx(sidecar))

		print(f"[run] premarket {iso_date}: PUBLISH — committing and pushing...", flush=True)
		committed = commit_and_push([sidecar_path, mdx_path], f"premarket {iso_date}")
		print(f"[run] premarket {iso_date}: committed={committed}. Verifying live...", flush=True)
		if committed:
			if verify_live(iso_date):
				ping_indexnow(iso_date)

		if data_quality != "full":
			send_alert("info", f"premarket published for {iso_date} — data_quality={data_quality}, missing={missing}")

		print(f"[run] premarket {iso_date}: done.", flush=True)
		return 0
	except Exception as exc:  # noqa: BLE001 - the top-level run boundary
		message = f"Pre-market run failed for {iso_date} at some stage: {exc}"
		print(f"[run] premarket {iso_date}: FAILED — {message}", flush=True)
		send_alert("high", message)
		return 1


if __name__ == "__main__":
	raise SystemExit(run(sys.argv[1]) if len(sys.argv) > 1 else run(today_ist().isoformat()))
