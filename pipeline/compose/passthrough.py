"""Passthrough discipline (ORCHESTRATION §8): source_name/source_url/
timestamp are copied from the pipeline's OWN input news items, by index —
never trusted from the LLM's output, which only ever supplies
headline_reworded and why_it_matters.
"""

from __future__ import annotations


class PassthroughError(Exception):
	pass


def reconstruct_news_items(llm_news: list[dict], input_news_items: list[dict]) -> list[dict]:
	by_index = {item["index"]: item for item in input_news_items}

	reconstructed = []
	for entry in llm_news:
		idx = entry.get("index")
		if idx not in by_index:
			raise PassthroughError(f"LLM referenced unknown news index {idx!r}")
		source = by_index[idx]
		reconstructed.append(
			{
				"headline_reworded": entry["headline_reworded"],
				"why_it_matters": entry["why_it_matters"],
				"source_name": source["source_name"],
				"source_url": source["source_url"],
				"timestamp": source["timestamp"],
			}
		)
	return reconstructed
