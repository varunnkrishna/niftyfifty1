"""Post-deploy verification + IndexNow ping (ORCHESTRATION §6c) — the last
pipeline stage, PUBLISH's own tail end. Runs after a successful commit+push;
Cloudflare Pages deploys on push, so this polls rather than assuming the
new page is live immediately.
"""

from __future__ import annotations

import os
import time

import requests

from pipeline.config import site_url
from pipeline.orchestrate.alert import send_alert

POLL_TIMEOUT_SECONDS = 180
POLL_INTERVAL_SECONDS = 15


def day_url(iso_date: str) -> str:
	y, m, d = iso_date.split("-")
	return f"{site_url()}/{y}/{m}/{d}/"


def verify_live(iso_date: str, expect_eod: bool = False, timeout: int = POLL_TIMEOUT_SECONDS) -> bool:
	"""Polls the live day URL for up to `timeout` seconds: expects HTTP 200
	and today's date string in the body; after an EOD run, additionally
	expects the EOD heading. Sends a `high` alert and returns False on
	failure — "committed but not live" (ORCHESTRATION §6c)."""
	url = day_url(iso_date)
	deadline = time.monotonic() + timeout

	last_error = ""
	while time.monotonic() < deadline:
		try:
			resp = requests.get(url, timeout=10)
			if resp.status_code == 200 and iso_date in resp.text and (not expect_eod or "EOD" in resp.text):
				return True
			last_error = f"status={resp.status_code}, date_present={iso_date in resp.text}"
		except requests.RequestException as exc:
			last_error = str(exc)
		time.sleep(POLL_INTERVAL_SECONDS)

	send_alert("high", f"Post-deploy verification failed for {url} — committed but not live. Last check: {last_error}")
	return False


def ping_indexnow(iso_date: str, timeout: int = 15) -> bool:
	"""SEO.md §3.4 — pings Bing/Yandex to index the new page within minutes
	instead of days. Best-effort: failure here is not alert-worthy on its
	own (the page is still live either way), just logged."""
	key = os.environ.get("INDEXNOW_KEY")
	if not key:
		print("INDEXNOW_KEY not set — skipping IndexNow ping.")
		return False

	url = day_url(iso_date)
	host = site_url().removeprefix("https://").removeprefix("http://")

	try:
		resp = requests.post(
			"https://api.indexnow.org/indexnow",
			json={"host": host, "key": key, "urlList": [url]},
			timeout=timeout,
		)
		resp.raise_for_status()
		print(f"IndexNow ping sent for {url}")
		return True
	except requests.RequestException as exc:
		print(f"IndexNow ping failed for {url}: {exc}")
		return False
