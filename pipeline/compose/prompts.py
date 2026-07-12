"""Prompt construction (ORCHESTRATION §8). The LLM only ever sees: a
numbered list of candidate news items (title, source, timestamp — no URL,
so it has nothing to echo back) and a rendered-text summary of the
already-computed numbers, for context only. It is never asked to produce
a number, and never given source_url to pass back (CLAUDE.md rule 1,
"passthrough discipline" — ORCHESTRATION §8).
"""

from __future__ import annotations

SYSTEM_PROMPT = """You are an editorial assistant for a financial news reference site. \
You reword news headlines into original phrasing and write short, factual connecting prose. \
You never invent numbers, facts, or figures that were not given to you. \
You never copy source sentences verbatim. \
You always respond with strict JSON only: no markdown code fences, no preamble, no commentary — \
just the JSON object itself."""


def _news_block(news_items: list[dict]) -> str:
	lines = []
	for item in news_items:
		lines.append(f"{item['index']}. [{item['source_name']}] {item['title']} ({item['timestamp']})")
	return "\n".join(lines)


def build_premarket_prompt(news_items: list[dict], setup_summary: str) -> tuple[str, str]:
	user_prompt = f"""Today's computed pre-market setup (context only — do not alter or restate these exact \
figures beyond what's needed; do not invent any numbers not shown here):

{setup_summary}

Candidate news items (numbered):

{_news_block(news_items)}

For EACH numbered item above, write:
- "headline_reworded": the headline in your own original words (not a copy of the original)
- "why_it_matters": one sentence on why this matters for today's market

Also write "market_expectations": a short paragraph (max 120 words) reading the setup above in \
plain English. The FIRST SENTENCE must directly state the outcome/expectation — no throat-clearing \
preamble. Do not include any numbers that are not already shown in the setup above. Do not include \
any URLs.

Respond with strict JSON only, in exactly this shape:
{{"news": [{{"index": 0, "headline_reworded": "...", "why_it_matters": "..."}}, ...], "market_expectations": "..."}}"""
	return SYSTEM_PROMPT, user_prompt


def build_eod_prompt(news_items: list[dict], setup_summary: str) -> tuple[str, str]:
	user_prompt = f"""Today's computed closing numbers (context only — do not alter or restate these exact \
figures beyond what's needed; do not invent any numbers not shown here):

{setup_summary}

Candidate news items (numbered):

{_news_block(news_items)}

For EACH numbered item above, write:
- "headline_reworded": the headline in your own original words (not a copy of the original)
- "why_it_matters": one sentence on why this mattered for today's session

Also write "conclusion": a short paragraph (max 120 words) synthesizing how the day went. The FIRST \
SENTENCE must directly state the outcome — no throat-clearing preamble. Do not include any numbers \
that are not already shown in the setup above. Do not include any URLs.

Respond with strict JSON only, in exactly this shape:
{{"news": [{{"index": 0, "headline_reworded": "...", "why_it_matters": "..."}}, ...], "conclusion": "..."}}"""
	return SYSTEM_PROMPT, user_prompt
