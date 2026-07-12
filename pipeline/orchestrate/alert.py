"""ntfy alerting (ORCHESTRATION §7). Silence = success — this is only ever
called for degraded/failed runs or maintenance nags, never a daily
"everything worked" ping.

Severity table:
  info        successful run with degradation (e.g. some inputs missing)
  high        run failed; page not published or not live
  missed-day  start-of-run check finds a gap in the archive
  config      maintenance needed (e.g. holiday calendar expiring)
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import requests

Severity = Literal["info", "high", "missed-day", "config"]

_PRIORITY = {"info": "default", "high": "urgent", "missed-day": "high", "config": "low"}

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_dotenv_if_present() -> None:
	env_path = REPO_ROOT / ".env"
	if not env_path.exists():
		return
	for line in env_path.read_text().splitlines():
		line = line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, _, value = line.partition("=")
		os.environ.setdefault(key.strip(), value.strip())


def send_alert(severity: Severity, message: str, timeout: int = 10) -> bool:
	"""Best-effort — a failed alert send must never crash the run itself
	(that would defeat the point). Returns True if the send succeeded."""
	_load_dotenv_if_present()
	topic = os.environ.get("NTFY_TOPIC")
	if not topic:
		print(f"[alert:{severity}] NTFY_TOPIC not set, printing instead: {message}")
		return False

	try:
		resp = requests.post(
			f"https://ntfy.sh/{topic}",
			data=message.encode("utf-8"),
			headers={"Title": f"Pipeline alert [{severity}]", "Priority": _PRIORITY[severity]},
			timeout=timeout,
		)
		resp.raise_for_status()
		return True
	except requests.RequestException as exc:
		print(f"[alert:{severity}] ntfy send failed: {exc}. Original message: {message}")
		return False
