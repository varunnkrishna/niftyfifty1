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

	if sidecar.eod_written:
		parts.append(_imports("SignalTable", "WarningBanner", "NewsList", "Eyebrow", "CloseTable"))
	else:
		parts.append(_imports("SignalTable", "WarningBanner", "NewsList", "Eyebrow", "AwaitingEod"))

	parts.append(f'\n<Eyebrow text="{premarket_eyebrow}" />')
	parts.append("\n## Pre-Market")
	parts.append("\n### Markets Data")
	parts.append(f"\n{{frontmatter.premarket.market_expectations}}")
	parts.append("\n<SignalTable premarket={frontmatter.premarket} />")
	parts.append("\n### Signal")

	if sidecar.premarket.bias_label is not None:
		parts.append(
			"\n**Bias: {`${frontmatter.premarket.bias_intensity} ${frontmatter.premarket.bias_label}`} · "
			"{frontmatter.premarket.bias_score > 0 ? '+' : ''}{frontmatter.premarket.bias_score}"
			"{frontmatter.premarket.conviction === 'reduced' ? ' · conviction reduced (VIX elevated)' : ''}**"
		)

	parts.append("\n<WarningBanner />")
	parts.append("\n### News")
	parts.append("\n<NewsList items={frontmatter.premarket.news} />")

	if sidecar.eod_written:
		parts.append('\n<hr class="section-divider" />')
		parts.append(f'\n<Eyebrow text="{eod_eyebrow}" />')
		parts.append("\n## EOD")
		parts.append("\n### Close")
		parts.append("\n{frontmatter.eod.conclusion}")
		parts.append(
			"\n<CloseTable\n"
			"\tnifty_close={frontmatter.eod.nifty_close}\n"
			"\tsensex_close={frontmatter.eod.sensex_close}\n"
			"\tbanknifty_close={frontmatter.eod.banknifty_close}\n"
			"/>"
		)
		parts.append(
			"\n{frontmatter.eod.advance_decline} · Leaders: {frontmatter.eod.sector_leaders.join(', ')} · "
			"Laggards: {frontmatter.eod.sector_laggards.join(', ')}"
		)
		parts.append("\n### News")
		parts.append("\n<NewsList items={frontmatter.eod.news} />")
	else:
		parts.append('\n<AwaitingEod expected="~16:15 IST" />')

	return "\n".join(parts) + "\n"


def render_weekend_body(sidecar: WeekendHolidaySidecar) -> str:
	return (
		f"{_imports('NewsList', 'Eyebrow')}\n"
		'\n<Eyebrow text="WEEKEND" />\n'
		"\nMarkets are closed today. Here's the market-relevant news.\n"
		"\n### News\n"
		"\n<NewsList items={frontmatter.news} />\n"
	)


def render_holiday_body(sidecar: WeekendHolidaySidecar) -> str:
	return (
		f"{_imports('NewsList', 'Eyebrow')}\n"
		"\n<Eyebrow text={`MARKET HOLIDAY · ${frontmatter.reason.toUpperCase()}`} />\n"
		"\nMarkets closed today — {frontmatter.reason}. No cash or derivatives session; "
		"regular trading resumes next session.\n"
		"\n### News\n"
		"\n<NewsList items={frontmatter.news} />\n"
	)
