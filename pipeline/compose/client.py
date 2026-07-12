"""OpenRouter/DeepSeek client (ORCHESTRATION §8). The only network call in
the entire pipeline that reaches an LLM — every other stage is
deterministic code (CLAUDE.md rule 1).
"""

from __future__ import annotations

import os
from pathlib import Path

import requests

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"
TEMPERATURE = 0.3  # editorial rewording, not creativity (ORCHESTRATION §8)
DEFAULT_TIMEOUT = 30

REPO_ROOT = Path(__file__).resolve().parents[2]


class ComposeError(Exception):
	"""Raised for anything that means COMPOSE cannot produce usable output —
	callers must treat this as "nothing publishes" (CLAUDE.md: nothing
	half-written is ever committed)."""


def _load_dotenv_if_present() -> None:
	"""Minimal .env loader — doesn't override real environment variables
	(e.g. the GitHub Actions secret in production). Local dev convenience
	only; stdlib-only, no need for a dependency for three lines."""
	env_path = REPO_ROOT / ".env"
	if not env_path.exists():
		return
	for line in env_path.read_text().splitlines():
		line = line.strip()
		if not line or line.startswith("#") or "=" not in line:
			continue
		key, _, value = line.partition("=")
		os.environ.setdefault(key.strip(), value.strip())


def api_key() -> str:
	_load_dotenv_if_present()
	key = os.environ.get("OPENROUTER_API_KEY")
	if not key:
		raise ComposeError("OPENROUTER_API_KEY is not set (env var or .env file)")
	return key


def call_llm(system_prompt: str, user_prompt: str, timeout: int = DEFAULT_TIMEOUT) -> str:
	"""One raw call. Returns the assistant's raw text content. Raises
	ComposeError on any HTTP/API-shape failure (never on JSON-parse
	failure of the *content* — that's the caller's retry loop's job)."""
	try:
		resp = requests.post(
			OPENROUTER_URL,
			headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"},
			json={
				"model": MODEL,
				"messages": [
					{"role": "system", "content": system_prompt},
					{"role": "user", "content": user_prompt},
				],
				"temperature": TEMPERATURE,
			},
			timeout=timeout,
		)
		resp.raise_for_status()
		data = resp.json()
		return data["choices"][0]["message"]["content"]
	except (requests.RequestException, KeyError, IndexError) as exc:
		raise ComposeError(f"OpenRouter call failed: {exc}") from exc
