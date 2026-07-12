import { existsSync, readdirSync } from 'node:fs';
import { fileURLToPath } from 'node:url';

// Date-tree sidebar (PLANNING.md §3): year → month → day, reverse-chronological,
// with counts. Built by walking the file system directly rather than the
// content-collection API, since URL/grouping is fully determined by the file
// path (src/content/docs/YYYY/MM/DD.mdx) per PLANNING §3's URL-determinism
// rule — and astro.config.mjs runs before the content layer is available.

const MONTH_NAMES = [
	'January', 'February', 'March', 'April', 'May', 'June',
	'July', 'August', 'September', 'October', 'November', 'December',
];

const docsDir = fileURLToPath(new URL('../content/docs/', import.meta.url));

function isDigitDir(name: string, length: number) {
	return name.length === length && /^\d+$/.test(name);
}

export function buildDateTreeSidebar() {
	if (!existsSync(docsDir)) return [];

	const years = readdirSync(docsDir, { withFileTypes: true })
		.filter((d) => d.isDirectory() && isDigitDir(d.name, 4))
		.map((d) => d.name)
		.sort((a, b) => b.localeCompare(a)); // newest year first

	return years.map((year) => {
		const yearDir = `${docsDir}${year}/`;
		const months = readdirSync(yearDir, { withFileTypes: true })
			.filter((d) => d.isDirectory() && isDigitDir(d.name, 2))
			.map((d) => d.name)
			.sort((a, b) => b.localeCompare(a)); // newest month first

		const monthItems = months.map((month) => {
			const monthDir = `${yearDir}${month}/`;
			const days = readdirSync(monthDir, { withFileTypes: true })
				.filter((d) => d.isFile() && /^\d{2}\.mdx$/.test(d.name))
				.map((d) => d.name.replace(/\.mdx$/, ''))
				.sort((a, b) => b.localeCompare(a)); // newest day first

			const dayItems = days.map((day) => ({
				label: day,
				slug: `${year}/${month}/${day}`,
			}));

			const monthName = MONTH_NAMES[Number(month) - 1];
			return {
				label: `${monthName} (${days.length})`,
				items: dayItems,
				collapsed: false,
			};
		});

		const totalDays = monthItems.reduce((sum, m) => sum + m.items.length, 0);
		return {
			label: `${year} (${totalDays})`,
			items: monthItems,
			collapsed: false,
		};
	});
}
