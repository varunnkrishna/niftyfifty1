"""Shared HTTP plumbing for source clients. A realistic desktop-browser
User-Agent is used everywhere — several sources (NSE, Yahoo, Moneycontrol)
reject requests carrying Python's default `python-requests/x.y` UA.
"""

from __future__ import annotations

import requests

USER_AGENT = (
	"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
	"(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

DEFAULT_TIMEOUT = 10


def new_session() -> requests.Session:
	s = requests.Session()
	s.headers.update(
		{
			"User-Agent": USER_AGENT,
			"Accept-Language": "en-US,en;q=0.9",
		}
	)
	return s
