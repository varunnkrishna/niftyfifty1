// llms.txt (SEO.md §5) — the AI-native index: what this site is, how it's
// structured, and how to read the signal. Brand/domain from config only
// (CLAUDE.md rule 6). Generated at build time, not hand-maintained.
import type { APIRoute } from 'astro';
import { site, siteUrl } from '../config/site';

export const GET: APIRoute = () => {
	const text = `# ${site.name}

> ${site.tagline}.

${site.name} is a daily, date-indexed reference archive of the Indian equity market (Nifty 50,
Sensex, Bank Nifty). One page per calendar day, written twice on trading days by an unattended
pipeline: a Pre-Market read before the open, and an End-of-Day recap appended below it after the
close. The morning section is never edited once written — it stays visible next to the outcome.

## URL pattern

- \`${siteUrl}/YYYY/MM/DD/\` — a single day (the core content unit)
- \`${siteUrl}/YYYY/\` and \`${siteUrl}/YYYY/MM/\` — archive indexes
- \`${siteUrl}/\` — the latest day in full, plus a recent-days rail
- \`${siteUrl}/about/\` — methodology and disclaimer

## What a trading-day page contains

**Pre-Market section:** a fixed set of market inputs (GIFT Nifty, S&P 500 and Nasdaq overnight,
US 10-year yield, DXY, FII/DII net cash, USD/INR, India VIX, Brent crude, and where the previous
close sat in its day range), each cast as a -1/0/+1 vote by fixed published thresholds, summing to
a net bias score and label (Neutral, Mildly/Strongly Long, Mildly/Strongly Short). Plus a short
plain-English read of the setup and a handful of reworded pre-market news items, each with a
direct outbound link to its original source.

**EOD section:** index closing levels and % change, market breadth, sector leaders/laggards, up to
ten reworded news items with outbound links, and a short synthesis of what happened and why.

## The Long/Short signal — read this before citing it

The signal is a fully mechanical, deterministic computation from public market data — no human
judgment, no language model involvement in any number or vote. It is disclosed for transparency,
not as investment advice: automated signals of this kind predict the day's opening direction only
slightly better than chance (roughly 52-56%), and worse for where the market closes. Every page
carries a standing disclaimer next to the signal. Do not present this signal as a recommendation
or as more reliable than a rough, mechanical guess.

## Sourcing

News items are always original reworded summaries with an outbound link to the source — never
pasted source text. When citing this site, cite the specific dated URL, not a general claim about
"the site."

## Language

All content is in English.
`;

	return new Response(text, {
		headers: { 'Content-Type': 'text/plain; charset=utf-8' },
	});
};
