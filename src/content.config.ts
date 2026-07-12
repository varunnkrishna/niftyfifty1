import { defineCollection, z } from 'astro:content';
import { docsLoader } from '@astrojs/starlight/loaders';
import { docsSchema } from '@astrojs/starlight/schema';

// Frontmatter shape for day pages (PLANNING.md §4) — the astro-build-time
// gate (ORCHESTRATION §6b). The pipeline's own pre-commit gate is the
// equivalent Pydantic schema at pipeline/validate/schema.py; this is
// intentional redundancy (ORCHESTRATION §6's "three layers"), not
// duplication to avoid. `type` is used as a soft discriminant via
// superRefine rather than z.discriminatedUnion() because <StarlightPage/>
// utility pages (homepage, /about/, year/month indexes) validate against
// this same schema and must be able to omit `type`/`date` entirely.

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
}).superRefine((data, ctx) => {
	// Utility pages (no `type`) skip day-page validation entirely.
	if (!data.type) return;

	if (!data.date) {
		ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['date'], message: 'date is required on day pages' });
	}

	if (data.type === 'trading-day') {
		if (!data.premarket) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['premarket'], message: 'premarket is required for trading-day pages' });
		}
		if (!data.data_quality) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['data_quality'], message: 'data_quality is required for trading-day pages' });
		}
		if (data.eod_written === undefined) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['eod_written'], message: 'eod_written is required for trading-day pages' });
		}
		if (data.eod_written && !data.eod) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['eod'], message: 'eod is required once eod_written is true' });
		}
		if (!data.eod_written && data.eod) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['eod'], message: 'eod must be absent until eod_written is true (CLAUDE.md rule 2)' });
		}
		if (data.premarket && (data.premarket.bias_label === null) !== (data.premarket.bias_score === null)) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['premarket', 'bias_label'], message: 'bias_label and bias_score must both be null (suppressed) or both set' });
		}
	} else if (data.type === 'weekend' || data.type === 'holiday') {
		if (!data.news || data.news.length === 0) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['news'], message: 'news is required for weekend/holiday pages' });
		}
		if (data.type === 'holiday' && !data.reason) {
			ctx.addIssue({ code: z.ZodIssueCode.custom, path: ['reason'], message: 'reason is required for holiday pages' });
		}
	}
});

export const collections = {
	docs: defineCollection({ loader: docsLoader(), schema: docsSchema({ extend: daySchema }) }),
};
