"""The COMPOSE-stage validation gates (ORCHESTRATION §8, PHASES.md Phase 5):
- no numbers in prose that don't appear in the fetched/computed metrics
- no verbatim-copied headlines (similarity check)
- no URLs in prose
- length caps on prose fields

These are heuristic, regex-based checks by design (ORCHESTRATION §8 says
"regex-scan prose for numerals and cross-check") — not a full NLP
solution, but enough to catch the failure modes that matter: an invented
figure, a pasted sentence, a leaked link.
"""

from __future__ import annotations

import difflib
import re

_NUMBER_RE = re.compile(r"\d[\d,]*\.?\d*")
_URL_RE = re.compile(r"https?://|www\.", re.IGNORECASE)

SIMILARITY_THRESHOLD = 0.7  # above this, a "reworded" headline is judged a verbatim copy
NEWS_PROSE_MAX_WORDS = 30  # "why_it_matters" (≤ 1 sentence)
PARAGRAPH_MAX_WORDS = 120  # market_expectations / conclusion (ORCHESTRATION §8)


def extract_numbers(text: str) -> set[str]:
	return {m.replace(",", "") for m in _NUMBER_RE.findall(text)}


def _number_variants(n: float) -> set[str]:
	if isinstance(n, bool):
		return set()
	variants = {str(n)}
	if isinstance(n, float):
		variants |= {str(round(n)), f"{n:.1f}", f"{n:.2f}", f"{abs(n):.1f}", f"{abs(n):.2f}", str(abs(round(n)))}
	elif isinstance(n, int):
		variants.add(str(abs(n)))
	return variants


def known_numbers_from(data) -> set[str]:
	"""Recursively collects every number appearing in a computed dict
	(premarket numbers or EOD numbers), in several plausible textual forms."""
	out: set[str] = set()
	if isinstance(data, dict):
		for v in data.values():
			out |= known_numbers_from(v)
	elif isinstance(data, list):
		for v in data:
			out |= known_numbers_from(v)
	elif isinstance(data, (int, float)) and not isinstance(data, bool):
		out |= _number_variants(data)
	return out


def check_no_invented_numbers(prose: str, known_numbers: set[str], field_name: str) -> list[str]:
	found = extract_numbers(prose)
	invented = found - known_numbers
	if invented:
		return [f"{field_name}: number(s) {sorted(invented)} not found in fetched/computed data"]
	return []


def check_no_urls(prose: str, field_name: str) -> list[str]:
	if _URL_RE.search(prose):
		return [f"{field_name}: contains a URL, which is not allowed in prose"]
	return []


def check_word_count(prose: str, max_words: int, field_name: str) -> list[str]:
	word_count = len(prose.split())
	if word_count > max_words:
		return [f"{field_name}: {word_count} words exceeds the {max_words}-word cap"]
	return []


def check_not_verbatim(reworded: str, original: str, field_name: str) -> list[str]:
	ratio = difflib.SequenceMatcher(None, reworded.lower().strip(), original.lower().strip()).ratio()
	if ratio >= SIMILARITY_THRESHOLD:
		return [f"{field_name}: reworded headline is {ratio:.0%} similar to the original — looks like a verbatim copy"]
	return []


def validate_news_item(reworded_item: dict, original_title: str, known_numbers: set[str]) -> list[str]:
	violations: list[str] = []
	violations += check_not_verbatim(reworded_item["headline_reworded"], original_title, "headline_reworded")
	violations += check_no_urls(reworded_item["headline_reworded"], "headline_reworded")
	violations += check_no_urls(reworded_item["why_it_matters"], "why_it_matters")
	violations += check_no_invented_numbers(reworded_item["why_it_matters"], known_numbers, "why_it_matters")
	violations += check_word_count(reworded_item["why_it_matters"], NEWS_PROSE_MAX_WORDS, "why_it_matters")
	return violations


def validate_paragraph(text: str, known_numbers: set[str], field_name: str) -> list[str]:
	violations: list[str] = []
	violations += check_no_urls(text, field_name)
	violations += check_no_invented_numbers(text, known_numbers, field_name)
	violations += check_word_count(text, PARAGRAPH_MAX_WORDS, field_name)
	return violations
