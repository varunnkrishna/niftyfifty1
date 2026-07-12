"""Renders the compute layer's numeric output as plain text for the LLM
prompt's context section (ORCHESTRATION §8: "for context only"). Never
fed back into any stored field — this is prompt input, not content.
"""

from __future__ import annotations


def render_premarket_summary(premarket_numbers: dict) -> str:
	lines = []
	for key in (
		"gift_nifty", "sp500_overnight", "nasdaq_overnight", "us10y_yield", "dxy",
		"fii_net_cash", "dii_net_cash", "usdinr", "prev_close_in_range", "india_vix", "brent",
	):
		m = premarket_numbers[key]
		if m.get("unavailable"):
			lines.append(f"{key}: unavailable")
			continue
		parts = [f"value={m.get('value')}"]
		if "delta_pct" in m:
			parts.append(f"delta_pct={m['delta_pct']:.2f}%")
		if "delta" in m:
			parts.append(f"delta={m['delta']}")
		if m.get("vote") is not None:
			parts.append(f"vote={m['vote']}")
		lines.append(f"{key}: {', '.join(parts)}")

	lines.append(f"conviction: {premarket_numbers['conviction']}")
	if premarket_numbers["bias_label"] is not None:
		lines.append(f"bias_score: {premarket_numbers['bias_score']}, bias_label: {premarket_numbers['bias_label']}")
	else:
		lines.append("bias: suppressed (insufficient data)")

	return "\n".join(lines)


def render_eod_summary(eod_numbers: dict) -> str:
	lines = [
		f"nifty_close: {eod_numbers['nifty_close']['value']} ({eod_numbers['nifty_close']['delta_pct']:+.2f}%)",
		f"sensex_close: {eod_numbers['sensex_close']['value']} ({eod_numbers['sensex_close']['delta_pct']:+.2f}%)",
		f"banknifty_close: {eod_numbers['banknifty_close']['value']} ({eod_numbers['banknifty_close']['delta_pct']:+.2f}%)",
	]
	if eod_numbers.get("advance_decline"):
		lines.append(f"advance_decline: {eod_numbers['advance_decline']}")
	if eod_numbers.get("sector_leaders"):
		lines.append(f"sector_leaders: {', '.join(eod_numbers['sector_leaders'])}")
	if eod_numbers.get("sector_laggards"):
		lines.append(f"sector_laggards: {', '.join(eod_numbers['sector_laggards'])}")
	return "\n".join(lines)
