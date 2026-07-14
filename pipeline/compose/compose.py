"""COMPOSE stage orchestration (ORCHESTRATION §8, PHASES.md Phase 5) — the
only place an LLM enters the pipeline. Both a JSON parse failure and a
content-validation failure (invented numbers, verbatim copy, URLs, length)
retry the call up to 2x with the error appended (3 attempts total), since
either is plausibly just a bad roll of the same LLM call. Only after all
attempts are exhausted does the run fail cleanly, same as any other
VALIDATE-stage failure (CLAUDE.md: nothing half-written is ever committed).
"""

from __future__ import annotations

from pipeline.compose.client import ComposeError, call_llm
from pipeline.compose.parsing import parse_llm_json
from pipeline.compose.passthrough import PassthroughError, reconstruct_news_items
from pipeline.compose.prompts import build_eod_prompt, build_premarket_prompt
from pipeline.compose.validate_prose import known_numbers_from, validate_news_item, validate_paragraph

MAX_RETRIES = 2  # up to 2 retries = 3 attempts total (ORCHESTRATION §8)


def compose_with_retry(
	system_prompt: str,
	user_prompt: str,
	news_items: list[dict],
	known_numbers: set[str],
	paragraph_field: str,
) -> tuple[list[dict], str]:
	last_error: str | None = None
	for _attempt_num in range(MAX_RETRIES + 1):
		prompt = user_prompt
		if last_error:
			prompt = (
				f"{user_prompt}\n\nYour previous response was rejected: {last_error}\n"
				"Respond again with STRICT valid JSON only — no markdown fences, no preamble. "
				"Every reworded headline must differ substantially in wording from the original headline."
			)
		raw_text = call_llm(system_prompt, prompt)
		try:
			parsed = parse_llm_json(raw_text)
		except Exception as exc:  # noqa: BLE001 - any parse failure triggers the retry loop
			last_error = f"JSON parse failed: {exc}. Raw response: {raw_text[:500]!r}"
			continue
		try:
			return _validate_and_reconstruct(parsed, news_items, known_numbers, paragraph_field)
		except ComposeError as exc:
			last_error = str(exc)
			continue

	raise ComposeError(f"COMPOSE failed after {MAX_RETRIES + 1} attempts, last error: {last_error}")


def _validate_and_reconstruct(parsed: dict, news_items: list[dict], known_numbers: set[str], paragraph_field: str) -> tuple[list[dict], str]:
	if "news" not in parsed or paragraph_field not in parsed:
		raise ComposeError(f"LLM JSON missing required key(s); expected 'news' and {paragraph_field!r}, got {list(parsed.keys())}")

	try:
		reconstructed = reconstruct_news_items(parsed["news"], news_items)
	except (PassthroughError, KeyError) as exc:
		raise ComposeError(f"LLM news output could not be reconciled with input items: {exc}") from exc

	violations: list[str] = []
	titles_by_index = {item["index"]: item["title"] for item in news_items}
	for entry, reconstructed_item in zip(parsed["news"], reconstructed):
		original_title = titles_by_index.get(entry.get("index"), "")
		violations += validate_news_item(reconstructed_item, original_title, known_numbers)

	paragraph = parsed[paragraph_field]
	violations += validate_paragraph(paragraph, known_numbers, paragraph_field)

	if violations:
		raise ComposeError("COMPOSE validation gate failed:\n" + "\n".join(violations))

	return reconstructed, paragraph


def compose_premarket(news_items: list[dict], premarket_numbers: dict, setup_summary: str) -> dict:
	system_prompt, user_prompt = build_premarket_prompt(news_items, setup_summary)
	known_numbers = known_numbers_from(premarket_numbers)
	news, market_expectations = compose_with_retry(system_prompt, user_prompt, news_items, known_numbers, "market_expectations")
	return {"news": news, "market_expectations": market_expectations}


def compose_eod(news_items: list[dict], eod_numbers: dict, setup_summary: str) -> dict:
	system_prompt, user_prompt = build_eod_prompt(news_items, setup_summary)
	known_numbers = known_numbers_from(eod_numbers)
	news, conclusion = compose_with_retry(system_prompt, user_prompt, news_items, known_numbers, "conclusion")
	return {"news": news, "conclusion": conclusion}
