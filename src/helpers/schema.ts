// JSON-LD structured data (SEO.md §4). Pure functions describing only what's
// actually on the page — every field reads from brand config (PLANNING §11),
// never a hardcoded site name/domain.

import { site, siteUrl } from '../config/site';

export interface Breadcrumb {
	name: string;
	url: string;
}

export function websiteSchema() {
	return {
		'@type': 'WebSite',
		'@id': `${siteUrl}/#website`,
		url: siteUrl,
		name: site.name,
		description: site.tagline,
		inLanguage: 'en',
	};
}

export function organizationSchema() {
	return {
		'@type': 'Organization',
		'@id': `${siteUrl}/#organization`,
		name: site.name,
		url: siteUrl,
	};
}

export function breadcrumbListSchema(items: Breadcrumb[]) {
	return {
		'@type': 'BreadcrumbList',
		itemListElement: items.map((item, i) => ({
			'@type': 'ListItem',
			position: i + 1,
			name: item.name,
			item: item.url,
		})),
	};
}

interface DayFrontmatter {
	title: string;
	description: string;
	date: string;
	type: 'trading-day' | 'weekend' | 'holiday';
	eod_written?: boolean;
	premarket?: Record<string, unknown>;
	eod?: { conclusion?: string };
}

// Pre-Market and EOD both write on trading days (PLANNING §2) — dateModified
// only differs from datePublished once the EOD write has actually landed,
// which is the freshness signal SEO.md §4 wants surfaced.
export function newsArticleSchema(fm: DayFrontmatter, pageUrl: string) {
	const datePublished = `${fm.date}T08:40:00+05:30`;
	const dateModified = fm.eod_written ? `${fm.date}T16:20:00+05:30` : datePublished;
	// Google's NewsArticle rich-result eligibility requires `image` — the
	// same build-time OG card doubles as this (SEO.md §2.7).
	const image = `${siteUrl}/og/${fm.date.replaceAll('-', '/')}.png`;

	return {
		'@type': 'NewsArticle',
		'@id': `${pageUrl}#article`,
		headline: fm.title,
		description: fm.description,
		image: [image],
		datePublished,
		dateModified,
		about: ['Nifty 50', 'Sensex', 'Indian equity markets'],
		publisher: { '@id': `${siteUrl}/#organization` },
		mainEntityOfPage: pageUrl,
		inLanguage: 'en',
	};
}

// Metrics as machine-parseable data, not just prose — a differentiator for
// AI extraction (SEO.md §4).
export function datasetSchema(premarket: Record<string, any>, fm: DayFrontmatter, pageUrl: string) {
	const votedKeys = [
		'gift_nifty', 'sp500_overnight', 'nasdaq_overnight', 'us10y_yield', 'dxy',
		'fii_net_cash', 'dii_net_cash', 'usdinr', 'prev_close_in_range', 'india_vix', 'brent',
	];

	const variableMeasured = votedKeys
		.map((key) => premarket[key] && { key, m: premarket[key] })
		.filter((entry): entry is { key: string; m: any } => Boolean(entry) && !entry!.m.unavailable)
		.map(({ key, m }) => {
			// unitText is only "percent" when delta_pct itself is the reported
			// value (metrics with no separate absolute level, e.g. sp500_overnight)
			// — a price/level (GIFT Nifty, DXY, ...) must never be mislabeled.
			const usingDeltaPctAsValue = m.value === undefined && m.delta_pct !== undefined;
			return {
				'@type': 'PropertyValue',
				name: key,
				value: m.value ?? m.delta_pct ?? m.delta ?? null,
				...(usingDeltaPctAsValue ? { unitText: 'percent' } : {}),
			};
		});

	return {
		'@type': 'Dataset',
		'@id': `${pageUrl}#dataset`,
		name: `Pre-market signal inputs — ${fm.date}`,
		description: "Machine-readable pre-market metrics and votes feeding the site's Long/Short signal.",
		variableMeasured,
	};
}

export function speakableSchema(cssSelectors: string[]) {
	return {
		'@type': 'WebPageElement',
		speakable: {
			'@type': 'SpeakableSpecification',
			cssSelector: cssSelectors,
		},
	};
}

export function jsonLdGraph(nodes: Array<object | null | undefined | false>) {
	return {
		'@context': 'https://schema.org',
		'@graph': nodes.filter(Boolean),
	};
}
