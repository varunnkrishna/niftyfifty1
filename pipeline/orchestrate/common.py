"""Shared helpers for the orchestration entrypoints — loading config/archive
state, and start-of-run hygiene (ORCHESTRATION §4: "every run starts with
git pull, then the missed-run check")."""

from __future__ import annotations

import json
import subprocess
from datetime import date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
from datetime import datetime

IST = ZoneInfo("Asia/Kolkata")


def today_ist() -> date:
	"""All scheduling logic is IST-internal (CLAUDE.md conventions) — crons
	are expressed in UTC, but "today" must always mean the IST calendar
	date, not the runner's local/UTC date."""
	return datetime.now(IST).date()

from pipeline.orchestrate.alert import send_alert
from pipeline.orchestrate.resolve import ResolverError, resolve

REPO_ROOT = Path(__file__).resolve().parents[2]
DAYS_DIR = REPO_ROOT / "data" / "days"
SIGNAL_CONFIG_PATH = REPO_ROOT / "data" / "signal-config.json"


def git_pull() -> None:
	subprocess.run(["git", "pull", "--ff-only"], cwd=REPO_ROOT, check=True)


def load_signal_config() -> dict:
	return json.loads(SIGNAL_CONFIG_PATH.read_text())


def load_day_sidecar(iso_date: str) -> dict | None:
	path = DAYS_DIR / f"{iso_date}.json"
	if not path.exists():
		return None
	return json.loads(path.read_text())


def load_prev_day_sidecar(today: date) -> dict | None:
	return load_day_sidecar((today - timedelta(days=1)).isoformat())


def missed_day_check(today: date) -> None:
	"""Does yesterday's expected page exist? (ORCHESTRATION §4)"""
	yesterday = today - timedelta(days=1)
	try:
		day_type, _ = resolve(yesterday)
	except ResolverError:
		return  # the resolver's own alert path handles a missing calendar

	if day_type == "weekend":
		return
	if load_day_sidecar(yesterday.isoformat()) is None:
		send_alert("missed-day", f"No page exists for {yesterday.isoformat()} ({day_type}).")


def select_news_items(raw_news: list[dict], limit: int) -> list[dict]:
	"""RSS items -> the indexed shape COMPOSE expects (ORCHESTRATION §8)."""
	return [
		{
			"index": i,
			"title": item["title"],
			"source_name": item["source_name"],
			"source_url": item["link"],
			"timestamp": item["published"],
		}
		for i, item in enumerate(raw_news[:limit])
	]


def write_json(path: Path, data: dict) -> None:
	path.parent.mkdir(parents=True, exist_ok=True)
	path.write_text(json.dumps(data, indent="\t", sort_keys=True) + "\n")
