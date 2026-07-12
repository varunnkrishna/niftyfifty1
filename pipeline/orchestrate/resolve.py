"""Day-type resolver (ORCHESTRATION §2) — the first step of every run.
`resolve(date) -> "trading" | "weekend" | "holiday"`, plus the holiday
calendar's own expiry check (ORCHESTRATION §9's `config` alert).
"""

from __future__ import annotations

import json
from datetime import date as date_type, timedelta
from pathlib import Path
from typing import Literal

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"

DayType = Literal["trading", "weekend", "holiday"]

EXPIRY_WARNING_WINDOW_DAYS = 14


class ResolverError(Exception):
	"""Raised when the day-type can't be determined at all — e.g. no holiday
	calendar exists for the year in question. ORCHESTRATION §2: alert rather
	than guess."""


def _calendar_path(year: int) -> Path:
	return DATA_DIR / f"nse-holidays-{year}.json"


def _load_holiday_calendar(year: int) -> dict | None:
	path = _calendar_path(year)
	if not path.exists():
		return None
	return json.loads(path.read_text())


def resolve(d: date_type) -> tuple[DayType, str | None]:
	"""Returns (day_type, holiday_reason). holiday_reason is only set when
	day_type == "holiday" (e.g. "Republic Day")."""
	if d.weekday() >= 5:  # Saturday=5, Sunday=6
		return "weekend", None

	calendar = _load_holiday_calendar(d.year)
	if calendar is None:
		raise ResolverError(
			f"No NSE holiday calendar found for {d.year} (expected {_calendar_path(d.year).name}) — "
			"holiday calendar expired. Add the file rather than guessing (ORCHESTRATION §2)."
		)

	for holiday in calendar["holidays"]:
		if holiday["date"] == d.isoformat():
			return "holiday", holiday["reason"]

	return "trading", None


def check_holiday_calendar_expiry(today: date_type) -> str | None:
	"""Proactive check (ORCHESTRATION §9 `config` alert): warns when the
	current year's calendar coverage is about to run out and next year's
	file isn't committed yet. Returns a warning message, or None if fine."""
	year_end = date_type(today.year, 12, 31)
	days_until_year_end = (year_end - today).days

	if days_until_year_end > EXPIRY_WARNING_WINDOW_DAYS:
		return None  # not close enough to the boundary to matter yet

	next_year_calendar = _load_holiday_calendar(today.year + 1)
	if next_year_calendar is not None:
		return None  # already handled

	expiry_date = year_end + timedelta(days=1)
	days_left = (expiry_date - today).days
	return (
		f"NSE holiday calendar for {today.year + 1} is not yet committed — "
		f"the current calendar's coverage runs out in {days_left} day(s) (on {year_end.isoformat()})."
	)
