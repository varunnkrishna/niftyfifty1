import { defineCollection, z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

// Draft frontmatter shape for day pages (PLANNING.md §4). This is Phase 1's
// "loose" schema — just enough shape for the fixtures to type-check and
// render. Phase 2 replaces this with the strict, discriminated-union Zod
// contract that gates the pipeline's writes (malformed JSON must fail the
// build loudly — PLANNING §4, CLAUDE.md "validation is a feature").

const votedMetric = z.object({
	value: z.union([z.string(), z.number()]).optional(),
	delta_pct: z.number().optional(),
	delta: z.number().optional(),
	vote: z.union([z.literal(-1), z.literal(0), z.literal(1)]).nullable(),
	unavailable: z.boolean().optional(),
});

const newsItem = z.object({
	headline_reworded: z.string(),
	why_it_matters: z.string(),
	source_name: z.string(),
	source_url: z.string().url(),
	timestamp: z.string(),
});

const closeMetric = z.object({
	value: z.number(),
	delta_pct: z.number(),
});

const daySchema = z.object({
	// Optional so <StarlightPage/> utility pages (homepage, /about/, year/month
	// indexes) — which are validated against this same schema — can omit them.
	// Real day pages always set both; Phase 2's strict validation gate enforces
	// that for pipeline-authored content specifically.
	date: z.string().optional(),
	type: z.enum(['trading-day', 'weekend', 'holiday']).optional(),
	reason: z.string().optional(), // holiday closure reason, e.g. "Republic Day"

	// Trading-day only — Pre-Market
	premarket: z
		.object({
			gift_nifty: votedMetric,
			sp500_overnight: votedMetric,
			nasdaq_overnight: votedMetric,
			us10y_yield: votedMetric,
			dxy: votedMetric,
			brent: votedMetric, // context note only, vote always null
			fii_net_cash: votedMetric,
			dii_net_cash: votedMetric,
			india_vix: votedMetric, // conviction dampener, vote always null
			usdinr: votedMetric,
			prev_close_in_range: votedMetric,
			bias_score: z.number().nullable(),
			bias_label: z.enum(['Long', 'Short', 'Neutral', 'Cautious']).nullable(),
			bias_intensity: z.enum(['Mildly', 'Strongly']).nullable().optional(),
			conviction: z.enum(['normal', 'reduced']).optional(),
			market_expectations: z.string().optional(),
			news: z.array(newsItem).optional(),
		})
		.optional(),
	data_quality: z.enum(['full', 'partial', 'outage']).optional(),
	missing: z.array(z.string()).optional(),
	eod_written: z.boolean().optional(),

	// Trading-day only — EOD
	eod: z
		.object({
			nifty_close: closeMetric,
			sensex_close: closeMetric,
			banknifty_close: closeMetric,
			advance_decline: z.string().optional(),
			sector_leaders: z.array(z.string()).optional(),
			sector_laggards: z.array(z.string()).optional(),
			news: z.array(newsItem).optional(),
			conclusion: z.string().optional(),
		})
		.nullable()
		.optional(),

	// Weekend / holiday only
	news: z.array(newsItem).optional(),
});

export const collections = {
	docs: defineCollection({ loader: docsLoader(), schema: docsSchema({ extend: daySchema }) }),
};
