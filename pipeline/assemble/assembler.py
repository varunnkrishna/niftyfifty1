"""The deterministic sidecar JSON -> MDX assembler (ORCHESTRATION §3, §11.2).

Same JSON in, byte-identical MDX out — this property is what makes phase
reruns safe (idempotency). No timestamps-of-generation, no non-deterministic
ordering anywhere in this module.
"""

from __future__ import annotations

from datetime import date as date_type

import yaml

from pipeline.validate.schema import TradingDaySidecar, WeekendHolidaySidecar, parse_sidecar
from pipeline.assemble.templates import (
	render_holiday_body,
	render_trading_day_body,
	render_weekend_body,
)

MONTH_ABBR = [
	"Jan", "Feb", "Mar", "Apr", "May", "Jun",
	"Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
]
MONTH_NAME = [
	"January", "February", "March", "April", "May", "June",
	"July", "August", "September", "October", "November", "December",
]


class _QuotedDumper(yaml.SafeDumper):
	"""Double-quotes any string scalar that would round-trip to something
	other than itself if left bare. Without this, PyYAML emits
	`2026-07-09` / `2026-07-09T08:12:00+05:30`-shaped strings unquoted,
	which most YAML frontmatter parsers (incl. the one Astro uses) then
	re-parse as native dates/timestamps instead of strings — silently
	breaking the `date: z.string()` / `timestamp: z.string()` contract.
	Plain strings (keys, prose, labels) stay unquoted for readability.
	"""


def _str_presenter(dumper: yaml.Dumper, data: str):
	try:
		reloaded = yaml.safe_load(data)
	except yaml.YAMLError:
		reloaded = None
	style = None if reloaded == data and isinstance(reloaded, str) else '"'
	return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


_QuotedDumper.add_representer(str, _str_presenter)


def _fmt_date_human(iso_date: str) -> str:
	d = date_type.fromisoformat(iso_date)
	return f"{d.day:02d} {MONTH_ABBR[d.month - 1]} {d.year}"


def _title_and_description(sidecar: TradingDaySidecar | WeekendHolidaySidecar) -> tuple[str, str]:
	human_date = _fmt_date_human(sidecar.date)

	if isinstance(sidecar, TradingDaySidecar):
		if sidecar.eod_written:
			eod = sidecar.eod
			assert eod is not None
			pct = eod.nifty_close.delta_pct
			pct_text = f"{'+' if pct > 0 else ''}{pct:.2f}%"
			bias = sidecar.premarket.bias_label or "Neutral"
			title = f"Nifty & Sensex — {human_date}"
			description = f"How markets closed — {human_date}. Nifty {pct_text}, bias was {bias}."
			return title, description

		title = f"Nifty outlook — {human_date}"
		if sidecar.premarket.bias_label is None:
			description = f"Nifty outlook — {human_date}. Signal suppressed today — too many inputs unavailable."
		else:
			intensity = sidecar.premarket.bias_intensity or ""
			description = f"Nifty outlook — {human_date}. Pre-market bias is {intensity} {sidecar.premarket.bias_label}.".replace("  ", " ")
		return title, description

	if sidecar.type == "weekend":
		title = f"Market News — {human_date}"
		description = f"Weekend market news — {human_date}. Markets are closed; a roundup of the day's market-relevant news."
		return title, description

	# holiday
	title = f"Markets Closed — {sidecar.reason} — {human_date}"
	description = f"Markets closed for {sidecar.reason} — {human_date}. A roundup of the day's market-relevant news."
	return title, description


def _metric_dict(m) -> dict:
	d = m.model_dump(mode="json", exclude_none=True)
	if d.get("unavailable") is False:
		del d["unavailable"]
	# The Zod schema's `vote` is nullable but not optional — the key must
	# always be present (possibly `null`), even though exclude_none above
	# drops it for non-voting/unavailable metrics.
	d["vote"] = m.vote
	return d


def _news_list(items) -> list[dict]:
	return [n.model_dump(mode="json") for n in items]


def _build_frontmatter(sidecar: TradingDaySidecar | WeekendHolidaySidecar, title: str, description: str) -> dict:
	fm: dict = {
		"title": title,
		"description": description,
		"date": sidecar.date,
		"type": sidecar.type,
	}

	if isinstance(sidecar, TradingDaySidecar):
		fm["data_quality"] = sidecar.data_quality
		fm["missing"] = list(sidecar.missing)
		fm["eod_written"] = sidecar.eod_written

		pm = sidecar.premarket
		fm["premarket"] = {
			**{key: _metric_dict(getattr(pm, key)) for key in (
				"gift_nifty", "sp500_overnight", "nasdaq_overnight", "us10y_yield", "dxy",
				"fii_net_cash", "dii_net_cash", "usdinr", "prev_close_in_range",
				"india_vix", "brent",
			)},
			"bias_score": pm.bias_score,
			"bias_label": pm.bias_label,
			"bias_intensity": pm.bias_intensity,
			"conviction": pm.conviction,
			"market_expectations": pm.market_expectations,
			"news": _news_list(pm.news),
		}

		if sidecar.eod_written:
			eod = sidecar.eod
			assert eod is not None
			fm["eod"] = {
				"nifty_close": eod.nifty_close.model_dump(mode="json"),
				"sensex_close": eod.sensex_close.model_dump(mode="json"),
				"banknifty_close": eod.banknifty_close.model_dump(mode="json"),
				"advance_decline": eod.advance_decline,
				"sector_leaders": list(eod.sector_leaders),
				"sector_laggards": list(eod.sector_laggards),
				"conclusion": eod.conclusion,
				"news": _news_list(eod.news),
			}
	else:
		if sidecar.type == "holiday":
			fm["reason"] = sidecar.reason
		fm["news"] = _news_list(sidecar.news)

	return fm


def assemble_mdx(raw_sidecar: dict) -> str:
	"""The one entrypoint: raw sidecar JSON dict -> complete MDX file text."""
	sidecar = parse_sidecar(raw_sidecar)
	title, description = _title_and_description(sidecar)
	frontmatter = _build_frontmatter(sidecar, title, description)

	yaml_text = yaml.dump(
		frontmatter,
		Dumper=_QuotedDumper,
		sort_keys=False,
		allow_unicode=True,
		width=1000,
		default_flow_style=False,
	)

	if isinstance(sidecar, TradingDaySidecar):
		body = render_trading_day_body(sidecar, premarket_eyebrow="PRE-MARKET · 08:40 IST", eod_eyebrow="EOD · 16:20 IST")
	elif sidecar.type == "weekend":
		body = render_weekend_body(sidecar)
	else:
		body = render_holiday_body(sidecar)

	return f"---\n{yaml_text}---\n\n{body}"


def content_path(iso_date: str) -> str:
	"""src/content/docs/YYYY/MM/DD.mdx path for a given date (PLANNING §3)."""
	y, m, d = iso_date.split("-")
	return f"src/content/docs/{y}/{m}/{d}.mdx"
