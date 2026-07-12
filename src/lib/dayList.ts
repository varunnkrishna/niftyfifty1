import type { CollectionEntry } from 'astro:content';

// Shared helpers for building the homepage / year / month index pages —
// one-line summaries per day, reverse-chronological sorting.

export function sortByDateDesc(entries: CollectionEntry<'docs'>[]) {
	return entries
		.slice()
		.sort((a, b) => (b.data.date ?? '').localeCompare(a.data.date ?? ''));
}

export function dayHref(date: string) {
	const [y, m, d] = date.split('-');
	return `/${y}/${m}/${d}/`;
}

export function daySummary(entry: CollectionEntry<'docs'>) {
	const d = entry.data as any;
	if (d.type === 'trading-day') {
		if (!d.eod_written) {
			return d.premarket?.bias_label
				? `Pre-market: ${d.premarket.bias_intensity ?? ''} ${d.premarket.bias_label}`.trim()
				: 'Awaiting EOD';
		}
		const pct = d.eod?.nifty_close?.delta_pct;
		const pctText = typeof pct === 'number' ? `${pct > 0 ? '+' : ''}${pct.toFixed(2)}%` : '—';
		return `Nifty ${pctText} · ${d.premarket?.bias_label ?? 'Neutral'}`;
	}
	if (d.type === 'weekend') return 'Weekend — news only';
	if (d.type === 'holiday') return `Market holiday — ${d.reason ?? ''}`;
	return '';
}
