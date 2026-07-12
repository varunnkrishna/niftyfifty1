"""Brand as a variable (PLANNING.md §11 / CLAUDE.md rule 6) — the Python
side. Reads the same /config/site.json that src/config/site.ts reads, so
there is exactly one place the brand name/domain/tagline are written,
shared by both languages. Never hardcode the domain elsewhere in the
pipeline (e.g. postdeploy verification, IndexNow, alerts).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parents[1]
_CONFIG_PATH = REPO_ROOT / "config" / "site.json"


class SiteConfig(TypedDict):
	name: str
	domain: str
	tagline: str


def load_site_config() -> SiteConfig:
	return json.loads(_CONFIG_PATH.read_text())


def site_url() -> str:
	return f"https://{load_site_config()['domain']}"
