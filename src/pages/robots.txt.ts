// robots.txt (SEO.md §2.6) — sitemap ref + an explicit AI-crawler allow
// list, since being read by AI is an explicit site goal. Generated at
// build time (not a static public/ file) so the domain always comes from
// site config, never a hardcoded string (CLAUDE.md rule 6).
import type { APIRoute } from 'astro';
import { siteUrl } from '../config/site';

const AI_CRAWLERS = [
	'GPTBot',
	'ChatGPT-User',
	'OAI-SearchBot',
	'ClaudeBot',
	'Claude-Web',
	'anthropic-ai',
	'PerplexityBot',
	'Perplexity-User',
	'Google-Extended',
	'CCBot',
	'Applebot-Extended',
	'Amazonbot',
	'Bytespider',
	'cohere-ai',
	'Diffbot',
];

export const GET: APIRoute = () => {
	const lines = [
		'User-agent: *',
		'Allow: /',
		'',
		'# Explicit AI-crawler allow list — being read and cited by AI is a goal',
		'# of this site (SEO.md §0, §2.6), not something to defend against.',
		...AI_CRAWLERS.flatMap((agent) => [`User-agent: ${agent}`, 'Allow: /', '']),
		`Sitemap: ${siteUrl}/sitemap-index.xml`,
	];

	return new Response(lines.join('\n'), {
		headers: { 'Content-Type': 'text/plain; charset=utf-8' },
	});
};
