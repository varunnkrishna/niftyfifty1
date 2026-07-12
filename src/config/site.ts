// Brand as a variable (PLANNING.md §11 / CLAUDE.md rule 6).
// The actual values live in /config/site.json — the ONE source of truth
// shared by both this TS site and the Python pipeline (pipeline/config.py
// reads the same file). Every template, meta tag, JSON-LD field, and
// llms.txt entry must import from here — never hardcode the brand.
import siteConfig from '../../config/site.json';

export const site = siteConfig as {
	name: string;
	domain: string;
	tagline: string;
};

export const siteUrl = `https://${site.domain}`;
