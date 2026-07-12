"""Strict-JSON parsing of the LLM's raw text output (ORCHESTRATION §8:
"strict JSON only — no markdown fences, no preamble"). DeepSeek sometimes
wraps JSON in ```json fences anyway despite instructions — stripped
defensively, but a parse failure past that is a real failure, not silently
patched further.
"""

from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_llm_json(raw_text: str) -> dict:
	"""Raises json.JSONDecodeError on malformed input — callers retry."""
	cleaned = _FENCE_RE.sub("", raw_text.strip()).strip()
	return json.loads(cleaned)
