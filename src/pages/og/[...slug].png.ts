// Build-time OG image generation (SEO.md §2.7): date + closes + bias, as a
// simple text card. The only place images are used on the whole site, and
// they're generated, not hand-made — zero runtime cost (SEO.md §6).
import { OGImageRoute } from 'astro-og-canvas';
import { getCollection } from 'astro:content';
import { site } from '../../config/site';

const entries = await getCollection('docs', (entry) => Boolean(entry.data.date));
const pages = Object.fromEntries(entries.map((entry) => [entry.id, entry.data as Record<string, any>]));

function ogDescription(data: Record<string, any>): string {
	if (data.type === 'trading-day' && data.eod_written && data.eod) {
		const pct = data.eod.nifty_close.delta_pct;
		const pctText = `${pct > 0 ? '+' : ''}${pct.toFixed(2)}%`;
		const bias = [data.premarket?.bias_intensity, data.premarket?.bias_label].filter(Boolean).join(' ') || 'Neutral';
		return `Nifty ${data.eod.nifty_close.value.toLocaleString('en-IN')} (${pctText}) · Bias: ${bias}`;
	}
	if (data.type === 'trading-day') {
		const bias = data.premarket?.bias_label
			? [data.premarket?.bias_intensity, data.premarket?.bias_label].filter(Boolean).join(' ')
			: 'Signal suppressed';
		return `Pre-market bias: ${bias}`;
	}
	if (data.type === 'holiday') return `Markets closed — ${data.reason}`;
	return 'Weekend — markets closed';
}

export const { getStaticPaths, GET } = await OGImageRoute({
	pages,
	// The route file's own `.png` suffix already supplies the extension —
	// the library's default getSlug (meant for /src/pages/*.astro paths)
	// would otherwise double it up (e.g. `2026/07/09.png.png`).
	getSlug: (path) => path,
	getImageOptions: (_path, data) => ({
		title: data.title,
		description: ogDescription(data),
		bgGradient: [[14, 14, 16]],
		border: { color: [38, 38, 42], width: 4 },
		font: {
			title: { color: [237, 237, 234], size: 64, weight: 'SemiBold' },
			description: { color: [154, 154, 162], size: 34 },
		},
		padding: 80,
	}),
});
