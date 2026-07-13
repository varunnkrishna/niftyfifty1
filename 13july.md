# 13 July — Session Summary & Project Map

Everything below happened across one continuous working session covering PHASES.md Phase 0 through the start of Phase 8 (launch + supervised week). This doc is a handoff/navigation note, not a spec — the six docs at repo root (CLAUDE.md, PLANNING.md, DESIGN.md, ORCHESTRATION.md, SEO.md, PHASES.md) remain the source of truth for *what the system should do*. This doc is for *what's actually been done, where things live, and what to check first if something breaks*.

## Quick project map

**Repo:** https://github.com/varunnkrishna/niftyfifty1 (branch: `main`)
**Live site:** https://nifty.varuntools.qzz.io/
**Host:** Cloudflare Pages, project `niftyfifty1` (Git-connected, auto-deploys on push to `main`, framework preset "Astro")

| Where | What |
|---|---|
| `CLAUDE.md`, `PLANNING.md`, `DESIGN.md`, `ORCHESTRATION.md`, `SEO.md`, `PHASES.md` | The spec. Read these first for *intended* behavior. |
| `config/site.json` | Single source of brand truth (name/domain/tagline) — read by both `src/config/site.ts` (Astro) and `pipeline/config.py` (Python). Change domain/brand here only. |
| `astro.config.mjs` | Starlight config; custom `head` array carries the Google Search Console verification meta tag. |
| `src/components/Head.astro` | Overrides Starlight's default head to inject per-page OG image tags. |
| `src/config/sidebar.ts` | Builds the date-tree sidebar from the filesystem. |
| `data/days/YYYY-MM-DD.json` | The sidecar JSON — permanent source of truth per trading day. `premarket` block is read-only after morning commit (CI-enforced). |
| `data/nse-holidays-2026.json` | 2026 NSE holiday calendar. Needs a yearly update (~Dec) — nagged by a `config`-severity alert if it expires. |
| `data/signal-config.json` | All vote thresholds/weights — tune here, never in code. |
| `pipeline/fetch/` | Retry/backoff/fallback core (`retry.py`), per-source HTTP clients (`sources/`), metric wiring (`metrics.py`), RSS layer (`rss.py`). |
| `pipeline/compute/` | Pure vote/bias-score functions, degradation ladder. No I/O. |
| `pipeline/compose/` | The only place the LLM (DeepSeek via OpenRouter) touches the pipeline — strict-JSON, passthrough discipline. |
| `pipeline/assemble/` | Deterministic sidecar JSON → MDX renderer. Never hand-edit the MDX output. |
| `pipeline/orchestrate/run_premarket.py` / `run_eod.py` / `run_news.py` | The three entrypoints GitHub Actions calls. FETCH→COMPUTE→COMPOSE→ASSEMBLE→VALIDATE→PUBLISH, idempotent (already-published date = no-op). |
| `pipeline/orchestrate/alert.py` | ntfy sender. Silence = success; only fires on degraded/failed runs or maintenance nags. |
| `pipeline/orchestrate/postdeploy.py` | Post-deploy live-verification polling + IndexNow ping. |
| `.github/workflows/premarket.yml` / `eod.yml` / `daily-news.yml` / `manual.yml` | The four GH Actions workflows. First three have **active `schedule:` cron triggers already** (see "Crons are already live" below) — `manual.yml` is `workflow_dispatch`-only, used for on-demand/debug runs. |
| `pipeline/tests/` | 89 pytest tests. Run with `.venv/bin/pytest pipeline/tests/ -q`. |

**GitHub Actions secrets set:** `OPENROUTER_API_KEY`, `NTFY_TOPIC` (=`niftyfiftyone-alerts-cfd50a68`), `INDEXNOW_KEY` (=`c4b9289e8b569d218ea69d173fd4cfd6`).

**ntfy alert topic:** `niftyfiftyone-alerts-cfd50a68` on ntfy.sh — subscribed on phone, confirmed real push notifications arrive (initial "not showing up" issue was just the app not syncing on first subscribe; a manual test push confirmed delivery works).

**Search engines:**
- Google Search Console: property `https://nifty.varuntools.qzz.io/`, verified via HTML meta tag (not the file method — see gotcha below), sitemap `sitemap-index.xml` submitted.
- Bing Webmaster Tools: imported directly from the verified GSC property (one click, no separate verification needed), sitemap already crawled successfully.

## What got built, Phases 0–7

**Phase 0 — Repo scaffold.** Astro + Starlight site, brand-as-config, `pipeline/`/`data/`/`.github/workflows/` skeleton, NSE 2026 holiday calendar (16 dates, cross-checked against two sources), first-pass `signal-config.json`.

**Phase 1 — Site shell.** Full DESIGN.md visual language: self-hosted Source Serif 4 / Geist Sans / Geist Mono, dark hairline system, the signal readout table, warning banner fixture. Six hand-written fixtures covering every page state — visually approved before Phase 2. Dynamic date-tree sidebar, homepage, year/month indexes, `/about/`.

**Phase 2 — Assembler & schemas.** Python `pipeline/assemble/` turns sidecar JSON into MDX deterministically (byte-identical on rerun, verified by test). Pydantic schema mirrors the Zod content-collection schema.

**Phase 3 — Fetch layer.** Retry/backoff/fallback core, HTTP clients for Yahoo Finance/FRED/Stooq/NSE/Moneycontrol, RSS layer. Live-verified: 10/11 metrics populated, 89 real news items.

**Phase 4 — Compute layer.** Pure vote functions reading `signal-config.json`, VIX conviction damping, bias-score aggregation, the full degradation ladder (suppress at ≥4 missing inputs).

**Phase 5 — Compose (LLM).** DeepSeek/OpenRouter, strict-JSON output, retry-on-parse-failure, passthrough discipline (LLM never sees or returns URLs), validation gates.

**Phase 6 — SEO wiring.** JSON-LD (NewsArticle, BreadcrumbList, Dataset, Speakable, WebSite/Organization), build-time OG images per day, `robots.txt`/`llms.txt` with the AI-crawler allow list, real chronological prev/next links. Lighthouse 99/100 mobile.

**Phase 7 — Workflows, CI, alerts.** Day-type resolver, three orchestration scripts, four GitHub Actions workflows, CI gate (build + premarket-immutability diff + Lighthouse), ntfy alerting, post-deploy verification + IndexNow ping.

**Testing status:** 89/89 pytest tests passing throughout.

## Phase 8 — going live (this session's second half)

**Repo, host, domain.** Created `varunnkrishna/niftyfifty1` on GitHub (merged a GitHub-auto-generated README rather than force-pushing over it). Created Cloudflare Pages project, connected to the repo — first deploy had no build command configured (fixed via the "Astro" framework preset, which auto-fills `npm run build` / `dist`). Pointed the custom domain `nifty.varuntools.qzz.io` at it (Cloudflare auto-created the CNAME). Added the three GitHub Actions secrets via the browser.

**Live pipeline debugging — the RSS timestamp bug.** First three manual `workflow_dispatch` runs of `premarket` all failed silently: exit code 1, zero log output, even after adding `PYTHONUNBUFFERED=1` and per-stage/per-attempt print statements everywhere in the fetch layer. Root cause was hiding in plain sight: the top-level `except` blocks in all three `run_*.py` entrypoints sent the exception to the ntfy alert but **never printed it to stdout** — so the GitHub Actions log genuinely had nothing to show, no matter how much logging was added upstream. Found the real error by pulling the raw alert history straight from ntfy.sh's JSON API (`curl https://ntfy.sh/<topic>/json?poll=1&since=all`), which showed:

```
trading-day.premarket.news.4.timestamp
  Value error, timestamp must be ISO 8601 (e.g. 2026-07-09T08:12:00+05:30)
  input_value='Mon, 13 Jul 2026 13:02:12 +0530'
```

feedparser's raw RSS `published` field is RFC 822 format, but the sidecar schema requires ISO 8601. Fixed in two commits (`171db0a`):
1. `pipeline/fetch/rss.py` now converts via feedparser's own `published_parsed`/`updated_parsed` struct_time instead of passing the raw string through.
2. All three `run_*.py` entrypoints now print the failure message to stdout before alerting, so this class of bug can never hide silently again.

Fourth manual run succeeded end-to-end: FETCH → COMPUTE (bias_score=6) → COMPOSE → VALIDATE → PUBLISH → committed → verified live → IndexNow ping sent, for `https://nifty.varuntools.qzz.io/2026/07/14/`. Full pipeline chain confirmed working on live infrastructure.

**ntfy alerting confirmed live.** The pipeline's `info`-severity alert (fired because `gift_nifty` was the one missing metric) was confirmed present in ntfy.sh's history immediately. Getting it to show as a real phone push notification took a bit of troubleshooting — the ntfy app had cached the topic's history at subscribe time and wasn't syncing new messages automatically; a manual `curl` test push (twice) confirmed that once the app is properly synced, real background push notifications (banner + buzz, no need to open the app) work correctly.

**Google Search Console.** Added property as URL-prefix (`https://nifty.varuntools.qzz.io/`). The recommended HTML-file verification method doesn't work on this host: Cloudflare Pages auto-redirects `/file.html` → `/file` (308, its own "clean URLs" behavior), and Google's file-verification check doesn't follow redirects. Switched to the HTML **meta tag** method instead — added via Starlight's `head` config in `astro.config.mjs`, renders on every page, zero JS (doesn't touch CLAUDE.md rule 7). Verified successfully. Submitted `sitemap-index.xml` (initial status "Couldn't fetch" right after submission is normal — Google hasn't crawled it yet, should resolve within a day).

**Security issues flag — "Harmful downloads."** GSC reported 1 security issue for the property, but **Sample URLs: N/A** — no actual offending URL on this site. Site has zero downloadable files and zero client-side JS, so this is almost certainly reputation carried over from `qzz.io` (a shared free dynamic-DNS domain) rather than anything this specific host serves. Requested a review with an explanation to that effect. **Status: pending Google's review** — worth checking back on.

**Bing Webmaster Tools.** Signed in with Google OAuth (explicit user approval obtained for both the sign-in and the separate "view Search Console data" grant). Used the "Import from Google Search Console" flow — one click imported the already-verified property and its sitemap, no separate Bing verification needed. Sitemap already shows "Success," 1 URL discovered.

## Decisions made this session

- **Deploy host:** Cloudflare Pages
- **Alert channel:** ntfy.sh
- **Canonical URL form:** trailing slash (Astro default)
- **Public signal labels:** more conservative than the private LeanSide engine — higher `|bias_score|` needed before "Strongly Long/Short," given the ~52–56% real-world accuracy
- **Domain:** subdomain `nifty.varuntools.qzz.io` (over registering a root domain)
- **GSC verification method:** HTML meta tag, not file upload (Cloudflare Pages redirect incompatibility — see above)
- **Supervised-week protocol adaptation:** discovered mid-session that `premarket.yml`/`eod.yml` crons have had active `schedule:` triggers since Phase 7 — they're not something to "enable" for Days 3–5, they already fire automatically. Decided to skip the artificial Days 1–2 "manual only" phase and instead watch/verify cron-fired runs from day one (see below).

## Known gaps / things to watch

- **GIFT Nifty has no working data source.** Every Yahoo ticker guess 404s; Moneycontrol blocks plain HTTP. Wired to always report `unavailable` rather than guess.
- **Moneycontrol blocks plain HTTP almost everywhere** (confirmed 403 via curl/requests regardless of headers, works in a real browser). Only India VIX has an implemented scraper.
- **Stooq's CSV endpoint sits behind a JS proof-of-work challenge** — falls through to missing.
- **Business Standard's RSS feed 403s** every plain-HTTP client. The other three feeds work.
- **EOD breadth (advance/decline) and sector leaders/laggards have no fetcher** — omitted rather than fabricated.
- **NSE was flaky mid-session** at one point — has a fallback by design.
- **GitHub Actions' free-tier scheduler can run cron-triggered workflows hours late** on a low-activity repo — confirmed: `premarket.yml`'s cron is `0 3 * * 1-5` UTC (08:30 IST) but its first live fire landed at ~11:49 IST, a ~3hr delay. Don't read "no run yet" as "cron is broken" without checking how much wall-clock slack GitHub typically takes.
- **GSC "Harmful downloads" security flag** — review requested, likely false positive from the shared `qzz.io` domain, not yet resolved by Google as of this writing.
- **GSC sitemap fetch status** — showed "Couldn't fetch" immediately after submission; should self-resolve on Google's next crawl, hasn't been re-checked yet.

## Current status: supervised-week protocol (PHASES.md Phase 8)

In progress. Because the crons are already live, the plan is: watch cron-fired premarket/EOD runs land cleanly for the next several trading days, run one deliberate failure drill (block a primary source, confirm the degraded page still publishes + an `info` alert fires, then revert), and once five consecutive clean trading-day cycles are observed, call the site autonomous per PHASES.md — dropping recurring human duties to ORCHESTRATION §9's three: yearly holiday-file update, weekly Search Console glance, on-alert rerun/fix.

A `CronCreate` session job is scheduled to check in around 16:23 IST today on whether `eod.yml`'s cron fired for 2026-07-13. Note: these scheduled check-ins are session-only — they die if this Claude Code session ends, so if picking this back up in a new session, just say so and the check can be done manually instead.
