// Brand as a variable (PLANNING.md §11 / CLAUDE.md rule 6).
// This is the ONLY place the site name, domain, and tagline may be written.
// Every template, meta tag, JSON-LD field, and llms.txt entry must import from here —
// never hardcode the brand into components, content, or comments.

export const site = {
	/** Current, temporary brand name. A rename should only ever touch this file. */
	name: "niftyfiftyone",
	/** Canonical domain, no protocol, no trailing slash. */
	domain: "niftyfiftyone.com",
	tagline: "A quiet reference for the Indian market",
} as const;

export const siteUrl = `https://${site.domain}`;
