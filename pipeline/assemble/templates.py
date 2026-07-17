"""MDX body templates — deterministic string rendering only, no timestamps
of generation (ORCHESTRATION §3). One function per page shape; the exact
component wiring here must match src/components/*.astro's props.
"""

from __future__ import annotations

from pipeline.validate.schema import TradingDaySidecar, WeekendHolidaySidecar

# Constant relative path from src/content/docs/YYYY/MM/DD.mdx to src/components/
# — always four levels up, since every day file sits at the same depth
# (PLANNING §3 "URL determinism").
_COMPONENTS = "../../../../components"


def _imports(*names: str) -> str:
	return "\n".join(f"import {name} from '{_COMPONENTS}/{name}.astro';" for name in names)


def render_trading_day_body(sidecar: TradingDaySidecar, premarket_eyebrow: str, eod_eyebrow: str) -> str:
	parts: list[str] = []

	# WarningBanner is composed inside SignalTable (CLAUDE.md rule 9 fixture).
	if sidecar.eod_written:
		parts.append(_imports("SignalTable", "NewsList", "Eyebrow", "CloseTable", "StructuredData", "PrevNextLinks"))
	else:
		parts.append(_imports("SignalTable", "NewsList", "Eyebrow", "AwaitingEod", "StructuredData", "PrevNextLinks"))

	parts.append("\n<StructuredData frontmatter={frontmatter} />")
	parts.append(f'\n<Eyebrow text="{premarket_eyebrow}" />')
	parts.append("\n## Pre-Market")
	parts.append("\n### Markets Data")
	parts.append('\n<p class="setup-copy">{frontmatter.premarket.market_expectations}</p>')
	parts.append("\n<SignalTable premarket={frontmatter.premarket} />")
	parts.append("\n### News")
	parts.append('\n<NewsList items={frontmatter.premarket.news} label="Pre-Market News" />')

	if sidecar.eod_written:
		parts.append('\n<hr class="section-divider" />')
		parts.append(f'\n<Eyebrow text="{eod_eyebrow}" />')
		parts.append("\n## EOD")
		parts.append("\n### Close")
		parts.append('\n<p class="eod-conclusion">{frontmatter.eod.conclusion}</p>')
		parts.append(
			"\n<CloseTable\n"
			"\tnifty_close={frontmatter.eod.nifty_close}\n"
			"\tsensex_close={frontmatter.eod.sensex_close}\n"
			"\tbanknifty_close={frontmatter.eod.banknifty_close}\n"
			"\tadvance_decline={frontmatter.eod.advance_decline}\n"
			"\tsector_leaders={frontmatter.eod.sector_leaders}\n"
			"\tsector_laggards={frontmatter.eod.sector_laggards}\n"
			"/>"
		)
		parts.append("\n### News")
		parts.append('\n<NewsList items={frontmatter.eod.news} label="EOD News" />')
	elif sidecar.eod_missed:
		parts.append("\n<AwaitingEod missed />")
	else:
		parts.append("\n<AwaitingEod expected=\"~16:15 IST\" />")

	parts.append("\n<PrevNextLinks date={frontmatter.date} />")

	return "\n".join(parts) + "\n"


def render_weekend_body(sidecar: WeekendHolidaySidecar) -> str:
	if sidecar.outage:
		# Backfilled outage page (ORCHESTRATION §4 recovery decision,
		# 2026-07-17): keep the calendar continuous, invent nothing.
		return (
			f"{_imports('Eyebrow', 'StructuredData', 'PrevNextLinks')}\n"
			"\n<StructuredData frontmatter={frontmatter} />"
			'\n<Eyebrow text="WEEKEND · OUTAGE" />\n'
			'\n<p class="setup-copy">The pipeline did not run this day — weekend news was not captured. '
			"This page was added afterward to keep the archive continuous; nothing on it is reconstructed.</p>\n"
			"\n<PrevNextLinks date={frontmatter.date} />\n"
		)
	return (
		f"{_imports('NewsList', 'Eyebrow', 'StructuredData', 'PrevNextLinks')}\n"
		"\n<StructuredData frontmatter={frontmatter} />"
		'\n<Eyebrow text="WEEKEND" />\n'
		'\n<p class="setup-copy">Markets are closed today. Here\'s the market-relevant news.</p>\n'
		"\n### News\n"
		'\n<NewsList items={frontmatter.news} label="Weekend News" />\n'
		"\n<PrevNextLinks date={frontmatter.date} />\n"
	)


def render_holiday_body(sidecar: WeekendHolidaySidecar) -> str:
	return (
		f"{_imports('NewsList', 'Eyebrow', 'StructuredData', 'PrevNextLinks')}\n"
		"\n<StructuredData frontmatter={frontmatter} />"
		"\n<Eyebrow text={`MARKET HOLIDAY · ${frontmatter.reason.toUpperCase()}`} />\n"
		"\n<p class=\"setup-copy\">Markets closed today — {frontmatter.reason}. No cash or derivatives session; "
		"regular trading resumes next session.</p>\n"
		"\n### News\n"
		'\n<NewsList items={frontmatter.news} label="Holiday News" />\n'
		"\n<PrevNextLinks date={frontmatter.date} />\n"
	)
