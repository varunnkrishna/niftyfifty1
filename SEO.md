# SEO.md — Search & AI Discoverability Plan

> Part of the six-doc handoff package (see README.md). Written plain — you don't need to be an SEO person to follow it.
> Pipeline-side SEO mechanics (IndexNow ping on publish, post-deploy verification, `dateModified` from the two-write model) are implemented per ORCHESTRATION.md §6c; SEO wiring is built in PHASES.md Phase 6.
> **Two buckets:** (1) *build-time SEO* the coding agent bakes in once, and (2) *operational SEO* — a short list of one-time setup steps **you** do in your own Google/Bing accounts (no repo can do these for you).
> **Brand is a variable** — every URL, title, and schema field reads from one config, so a future rename doesn't break anything.

---

## 0. The strategy in one line

Don't fight Moneycontrol/Groww for "nifty today". **Win the long tail your date-archive produces for free:** "nifty outlook 14 july 2026", "why did sensex fall today", "fii dii data 11 july", "market prediction tomorrow". Low competition each, compounding daily, and it's *exactly* what the site already generates. Every trading day = one new page targeting a fresh dated query. That's the whole game.

A second, equal goal: **be citable by AI** (ChatGPT, Perplexity, Copilot). That's a slightly different game from Google and depends heavily on **Bing** (see §3) plus clean structured data (§4) and `llms.txt` (§5).

---

## 1. How modern search actually works (30-second version)

Search in 2026 is **vectorized** — engines convert your text into meaning, not exact-word matches. Practical consequences:
- **Don't keyword-stuff.** Writing "nifty prediction" ten times does nothing. Covering the day *clearly and completely* (what moved, why, the data, the sources) ranks you for hundreds of related phrasings you never typed.
- **Titles and descriptions still matter** — because *humans* read them in the results and decide whether to click. So: honest, specific, human titles. Not robotic keyword strings.

This suits you: an automated site that writes a thorough, well-structured daily recap is doing the single most important thing already.

---

## 2. Build-time SEO — what the agent bakes in (ranked by impact)

The coding agent wires these once into layouts/helpers; every page inherits them. None of them ship JavaScript to the browser (§6).

1. **Canonical URL on every page.** Biggest win for least effort. One `<link rel="canonical">` computed from the page path, so trailing-slash / query-param variants don't split your ranking. **Pick one URL form and 301 everything else to it** (decide trailing-slash vs not, once).
2. **One `<h1>` per page, logical heading order.** The day's title is the H1; Pre-Market / EOD are H2s. Never skip levels.
3. **Unique `<title>` + meta description per page**, generated from the date + the freshest section. Lead with the live intent: morning → "Nifty outlook — 11 Jul 2026", after close → "How markets closed — 11 Jul 2026". Both on one URL; the meta updates on the EOD write (this is why `dateModified` matters).
4. **JSON-LD structured data** (see §4) — from a single `src/helpers/schema.ts`, never hand-copied into pages.
5. **Sitemap** via `@astrojs/sitemap` — set the site URL in config, reference `sitemap-index.xml` in `robots.txt`, done. Auto-includes every dated route. Use **per-collection chunks** so you can tell at a glance whether trading-day pages vs weekend pages are indexing.
6. **`robots.txt`** — allow crawlers, point to the sitemap, and **explicitly allow the 2026 AI crawler list** (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, CCBot, etc.) since being read by AI is an explicit goal.
7. **Open Graph + X/Twitter card meta** — per page, so shared links look right. Since the site has no images, use a **build-time generated OG image** (a simple text OG card: date + Nifty/Sensex close + bias) so shares aren't blank. This is the *one* place images are allowed, and they're generated, not hand-made.
8. **Breadcrumb JSON-LD** — Home › 2026 › July › 11. Reinforces the date hierarchy to engines and can show in results.
9. **`dateModified`** shown to readers when it differs from publish (morning vs EOD) — a real freshness signal, and honest.
10. **First paragraph = the answer.** Each section opens with the outcome in plain words ("Nifty closed down 0.8% at 24,102, dragged by IT and banks"), not a preamble. Both readers and AI extractors grab that first line.
11. **Descriptive internal links.** Link day-to-day ("previous session", "next session") and month indexes with real anchor text, not "click here". The date tree already does most of this.
12. **`noindex` the 404 and any utility pages.** Keep the index clean — only real content pages in the sitemap.
13. **Content-collection Zod schemas** (already in PLANNING.md §4) double as SEO insurance: a page missing a title or date *won't build*, so you can't accidentally ship an un-optimized page.

---

## 3. Operational SEO — your one-time setup (do these yourself, in order)

These need your accounts. Budget ~30–45 minutes total, once. No coding.

1. **Buy/point the domain** and deploy so the site is live at `https://niftyfiftyone.com` (one canonical host — pick www or non-www and redirect the other).
2. **Google Search Console** — add the property, verify ownership (DNS TXT record is easiest), **submit `sitemap-index.xml`**. This is how Google learns you exist and how you'll watch pages get indexed.
3. **Bing Webmaster Tools** — same thing for Bing. *Do not skip this* — **Bing's index feeds ChatGPT and Copilot**, so your "good for AI" goal partly lives or dies here. You can import settings from Search Console in one click.
4. **IndexNow** (optional, high value for a daily site) — a ping protocol so Bing/Yandex index new pages within minutes of publish instead of days. The agent can ping it on each deploy; you just generate a key once. Great fit because you publish twice daily.
5. **Ongoing habit (10 min/week, not more):** open Search Console, look at which dated queries are bringing impressions, note which recap topics get traction. That's your *only* ongoing SEO task. You're not optimizing pages by hand — you're learning what your audience searches so future automation can lean into it.

---

## 4. Structured data (JSON-LD) — the plan

Generated from one helper, describing only what's actually on the page (fake/duplicated schema *hurts* trust). Per day page:

- **`NewsArticle`** (or `Article`): `headline`, `datePublished`, `dateModified` (the two writes make this meaningful), `about` (Nifty 50, Sensex, Indian equity markets), `publisher` (from brand config).
- **`BreadcrumbList`**: the date hierarchy.
- **`Dataset` semantics** on the metrics block — so the numbers (Nifty close, FII/DII, VIX) are machine-parseable as data, not just prose. This is a differentiator for AI extraction.
- **`Speakable`** on the conclusion — marks the plain-English summary as the part voice assistants/AI should read aloud or quote.
- **Site-level `WebSite` + `Organization`** once, in the root layout.
- Every outbound news link carries clear citation semantics (you're a citation hub — lean into it).

Validate with Google's Rich Results Test before launch and after any schema change.

---

## 5. `llms.txt` — the AI-native index

A plain-text file at the site root that tells AI agents what the site is and how to use it. For you it should state: what niftyfiftyone is, the URL pattern (`/YYYY/MM/DD/`), what each day contains (pre-market data + signal, EOD recap + top-10 news with sources), **the Long/Short signal's meaning and its "automated guess, not advice" caveat**, and the content language (English). Optionally a build-time `llms-full.txt` with recent days inlined. This is cheap, static, and directly serves the "citable by AI" goal.

---

## 6. Keeping it fast — the GitHub-repos question, answered

Your instinct is exactly right: **speed is a ranking factor and an AI-crawlability factor, so nothing may slow the site.** The rule that makes this easy:

> **Every SEO tool here is build-time. Zero of them ship JavaScript to the browser.** A static Astro page with no client JS is already near-perfect on Core Web Vitals; the discipline is *keeping* it that way.

**Safe to add (build-time only, zero runtime weight):**
- `@astrojs/sitemap` — sitemap generation (official).
- A schema helper — either hand-rolled `src/helpers/schema.ts`, or a maintained JSON-LD graph library that runs **at build** (e.g. an Astro SEO-graph integration that emits `<Seo>` tags, schema, IndexNow, and `llms.txt`). Evaluate one vs hand-rolling at execution time; hand-rolled is lighter, a library is more complete.
- **Pagefind** — search index built at build time; its small JS loads only on the search page, not every page. Acceptable.
- Build-time **OG image generation** (Satori/`astro-og-canvas`) — runs during build, outputs static PNGs. No runtime cost.

**Never add (these quietly wreck the performance budget):**
- Heavy analytics (GA4 with everything on). If you want analytics, use a **lightweight, cookieless** option (Plausible/Umami) — one small script, or self-host. Better yet, read traffic from Search Console and skip client analytics entirely for v1.
- Chat widgets, consent-banner bloat, tag managers, A/B tools, ad scripts.
- Any React/Vue island that isn't genuinely interactive. Your pages are text — they should hydrate *nothing* by default.
- Multiple font families/weights. You have three families (Source Serif 4, Geist Sans, Geist Mono — DESIGN.md §Typography) — subset them, `font-display: swap`, self-host, and don't add a fourth.
- Client-side data fetching for market numbers. Numbers are baked in at build by the agent, never fetched in the browser.

**Guardrail to write into the build:** a Lighthouse/CWV check in CI that fails the build if performance drops below ~95. Keeps the discipline automatic instead of relying on memory.

---

## 7. Keyword & content strategy (tied to your structure)

You don't "do keywords" manually — the structure does it. But the agent's writing should naturally cover these intent clusters, because *clear coverage* (not stuffing) is what ranks:

- **Dated outlook:** "nifty outlook [date]", "market prediction tomorrow", "share market opening today" → served by the Pre-Market section + signal.
- **Explanatory:** "why did nifty/sensex fall/rise today", "reason for market fall today" → served by the EOD conclusion naming the drivers.
- **Data lookups:** "fii dii data today", "india vix today", "usd inr today" → served by the metrics block (and the `Dataset` schema makes these extractable).
- **Event-driven:** whatever actually moved that day (a stock, a policy, a global cue) → served by the reworded top-10 news + outbound links.

Two content rules that carry disproportionate SEO weight, for the agent spec:
1. **Lead every section with the answer**, in plain English, in the first sentence.
2. **Reworded summaries only, always with the source link.** Original wording avoids duplicate-content penalties; the outbound link makes you a citation hub instead of a scraper. This is both a legal and an SEO position.

---

## 8. What NOT to spend effort on (v1)

- Backlink chasing / guest posts — skip early; let the compounding dated pages and AI citations build authority first.
- Tags/categories taxonomy — the **date hierarchy is your only taxonomy**. Don't add tags; they add clutter without navigational value for a daily archive.
- Manual per-page optimization — the templates do it uniformly. If you're editing single pages for SEO, something's wrong with the template instead.
- Vanity keywords ("nifty today") as a *target* — you'll pick up some of that traffic as authority grows, but don't design for it.

---

## 9. Launch-day SEO checklist (one screen)

- [ ] One canonical host (www or non-www), other 301s to it
- [ ] Canonical tag on every page
- [ ] `sitemap-index.xml` building + linked in `robots.txt`
- [ ] `robots.txt` allows AI crawler list
- [ ] JSON-LD (`NewsArticle` + `BreadcrumbList` + `Dataset`) validating in Rich Results Test
- [ ] `llms.txt` at root
- [ ] Unique title + meta description per page, updating on EOD write
- [ ] Build-time OG image per page
- [ ] Google Search Console verified + sitemap submitted
- [ ] Bing Webmaster Tools verified + sitemap submitted
- [ ] IndexNow key set + ping on deploy (optional but recommended)
- [ ] Lighthouse ≥ 95 gate in CI
- [ ] 404 + utility pages `noindex`
