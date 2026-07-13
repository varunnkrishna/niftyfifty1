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
			// Google Search Console site-ownership verification (HTML tag method —
			// the HTML-file method redirects through Cloudflare Pages' automatic
			// .html-extension-stripping, which breaks Google's no-redirect check).
			head: [
				{
					tag: 'meta',
					attrs: { name: 'google-site-verification', content: '_sTKP2ordN6n8z1OxcLlfa1b8ctHR_3CIA5xteDhenE' },
				},
			],
			// Date-tree sidebar: year → month → day, reverse-chron, with counts
			// (PLANNING §3) — built from the filesystem, see src/config/sidebar.ts.
			sidebar: buildDateTreeSidebar(),
			// Starlight's built-in prev/next footer follows sidebar order, which
			// is reverse-chronological (newest first) — that makes its "next"
			// point to an *older* day, backwards from calendar sense. Disabled
			// in favor of PrevNextLinks.astro, which uses real chronological
			// order (SEO.md §2.11).
			pagination: false,
			customCss: ['./src/styles/fonts.css', './src/styles/tokens.css', './src/styles/skin.css'],
			// Per-page og:image (SEO.md §2.7) needs the current page's date,
			// which Starlight's static `head` config can't compute — see
			// src/components/Head.astro.
			components: { Head: './src/components/Head.astro' },
		}),
	],
});
