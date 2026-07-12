// @ts-check
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import { site, siteUrl } from './src/config/site.ts';

// https://astro.build/config
export default defineConfig({
	site: siteUrl,
	// Astro's default (directory-style output, e.g. /2026/07/11/) — the site's
	// chosen canonical URL form. Do not change without updating SEO canonical logic.
	integrations: [
		starlight({
			title: site.name,
			description: site.tagline,
			// Date-tree sidebar (year → month → day) is built in Phase 1 from the
			// content collection — intentionally empty here.
			sidebar: [],
		}),
	],
});
