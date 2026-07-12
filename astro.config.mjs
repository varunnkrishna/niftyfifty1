// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { site, siteUrl } from './src/config/site.ts';
import { buildDateTreeSidebar } from './src/config/sidebar.ts';

// https://astro.build/config
export default defineConfig({
	site: siteUrl,
	// Astro's default (directory-style output, e.g. /2026/07/11/) — the site's
	// chosen canonical URL form. Do not change without updating SEO canonical logic.
	integrations: [
		starlight({
			title: site.name,
			description: site.tagline,
			// Date-tree sidebar: year → month → day, reverse-chron, with counts
			// (PLANNING §3) — built from the filesystem, see src/config/sidebar.ts.
			sidebar: buildDateTreeSidebar(),
			customCss: ['./src/styles/fonts.css', './src/styles/tokens.css', './src/styles/skin.css'],
		}),
	],
});
