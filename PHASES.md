# PHASES.md — Build Order & Acceptance Gates

> The execution sequence for Claude Code. Expands ORCHESTRATION.md §11 into full phases.
> **The rule:** a phase is done when every acceptance box checks. Do not start the next phase before the gate passes. If a phase reveals a spec contradiction, stop and surface it — don't improvise around it.
> Site behavior: PLANNING.md · Visuals: DESIGN.md · Pipeline: ORCHESTRATION.md · Discoverability: SEO.md · Standing rules: CLAUDE.md.

---

## Phase 0 — Repo scaffold & brand config

**Goal:** an empty-but-correct skeleton where every later phase has an obvious home.

**Deliverables**
- Repo layout per ORCHESTRATION.md §10 (`pipeline/`, `data/`, `src/`, `.github/workflows/` as empty stubs).
- Astro + Starlight installed, static output, builds clean.
- **Brand config** (`src/config/site.ts`): name, domain, tagline — the only place the brand exists (PLANNING §11).
- `data/nse-holidays-2026.json` populated from NSE's published list.
- `data/signal-config.json` with the LeanSide vote thresholds/weights (ORCHESTRATION §9).

**Acceptance**
- [ ] `npm run build` succeeds on the empty shell.
- [ ] `grep -ri "niftyfiftyone" src/ --exclude-dir=config` returns nothing — brand appears only in config.
- [ ] Holiday file parses; contains ≥ 12 dates for 2026.

---

## Phase 1 — Site shell from fixtures (design before pipeline)

**Goal:** the complete visual site, rendering from **hand-written sidecar JSON fixtures** — so DESIGN.md is nailed against stable data before any fetching exists, and Varun can visually approve every page state.

**Deliverables**
- Full DESIGN.md skin: dark hairline system, three-column shell, Source Serif 4 / Geist Sans / Geist Mono self-hosted + subset, type scale, color tokens.
- Signal readout table (the signature element) per DESIGN.md.
- **Five fixtures** in `data/days/`: (1) full trading day with EOD, (2) trading day awaiting EOD, (3) weekend, (4) NSE holiday, (5) degraded day — 2 inputs missing — plus a variant with signal suppressed.
- Date-tree sidebar, on-this-page ToC, homepage (latest day in full + recent-days rail), month/year indexes, `/about/`.
- Mobile collapse behavior per DESIGN.md.

**Acceptance**
- [ ] All five fixture states render exactly per DESIGN.md §Page states (awaiting-EOD placeholder line, `—`/unavailable markers, suppressed-signal line, holiday reason).
- [ ] Warning banner renders adjacent to every signal display, including suppressed state.
- [ ] Zero client-side JS on day pages (Pagefind's JS only on search interaction).
- [ ] Red/green appear only on % changes and votes; grep the CSS to confirm no other use of `--up`/`--down`.
- [ ] No layout shift when the awaiting-EOD fixture is swapped for the full-day fixture.
- [ ] Lighthouse ≥ 95 (performance) on a fixture day page, mobile profile.
- [ ] **Human gate: Varun visually approves the five states before Phase 2.**

---

## Phase 2 — Assembler & schemas

**Goal:** the deterministic JSON → MDX renderer and the Zod contracts that gate everything.

**Deliverables**
- Zod schemas for trading-day / weekend-holiday sidecar JSON (PLANNING §4 field sets + `data_quality`, `missing[]`).
- Assembler: sidecar JSON → frontmatter-driven MDX, stable key order, no generation timestamps in content.
- Content-collection schemas so a bad MDX fails the Astro build.

**Acceptance**
- [ ] Assembling the same JSON twice → **byte-identical** MDX (this property is what makes reruns safe; test it explicitly).
- [ ] Each of ~6 deliberately malformed JSONs (missing date, news item without `source_url`, wrong type) fails schema validation with a clear error.
- [ ] Assembling fixture (2) then fixture (1) for the same date changes only the EOD region + `eod_written` + meta — verified by diff.

---

## Phase 3 — Fetch layer

**Goal:** every metric and feed in ORCHESTRATION §5a, with retries, fallbacks, and honest missing-markers.

**Deliverables**
- Fetchers per metric with primary + fallback sources; browser-like session handling for NSE.
- Retry policy: 3 attempts, backoff 5s/15s/45s, then fallback, then `missing`.
- RSS layer for the four feeds; a dead feed is a warning, not a failure.
- Output: a raw-fetch JSON recording value, source used, and `missing[]`.

**Acceptance**
- [ ] Live run at any hour produces a raw-fetch JSON with ≥ 9 of 11 metrics populated.
- [ ] Forcing a primary source to fail (mock/network block) demonstrably exercises fallback → then missing-marker.
- [ ] No fetched value is ever transformed by an LLM anywhere in this layer (it doesn't exist here — assert by code review).

---

## Phase 4 — Compute layer (signal engine)

**Goal:** LeanSide rules as pure functions reading `signal-config.json`.

**Deliverables**
- Vote functions per input (PLANNING §5 rules: GIFT ±0.3%, overnight US, US10Y, DXY, FII/DII, USD-INR, prev-close-in-range).
- VIX conviction dampener + Brent context note (non-voting).
- `bias_score`, `bias_label`, conviction; degradation ladder from ORCHESTRATION §5b including the **≥ 4-missing suppression**.

**Acceptance**
- [ ] Unit tests: every vote rule at, above, and below its threshold; missing input → vote 0.
- [ ] Test: 4 missing directional inputs → signal suppressed; 3 missing → published with `data_quality: "partial"`.
- [ ] Changing a threshold in `signal-config.json` changes behavior with **zero code edits**.

---

## Phase 5 — Compose (LLM) & validation gates

**Goal:** the only LLM touchpoint, fenced by machine checks (ORCHESTRATION §8).

**Deliverables**
- OpenRouter/DeepSeek call: strict-JSON output, temp ~0.3, retry-on-parse-failure ×2 with error appended.
- Passthrough discipline: `source_name`/`source_url`/`timestamp` copied from pipeline input, never from LLM output.
- Validation gates: numerals-in-prose cross-check against fetched metrics; reworded-headline similarity check; no URLs in prose; length caps; first-sentence-is-the-answer prompt rule (SEO §7).
- Full local VALIDATE stage (ORCHESTRATION §6a) wired before any commit.

**Acceptance**
- [ ] A mocked LLM response containing an invented number is caught and fails validation.
- [ ] A mocked verbatim-copy headline is caught by the similarity check.
- [ ] Malformed JSON from the LLM never reaches a commit (retries, then run fails cleanly).
- [ ] End-to-end dry run (fetch → compute → compose → assemble → validate) produces a valid, committed-nothing day file locally.

---

## Phase 6 — SEO wiring

**Goal:** everything in SEO.md §2 and §4–5, all build-time, zero browser JS.

**Deliverables**
- Canonical URL helper (one URL form, chosen per ORCHESTRATION §12.3); unique title/meta per page, leading with the freshest section.
- `src/helpers/schema.ts`: `NewsArticle` (+ `dateModified` from the two writes), `BreadcrumbList`, `Dataset` on the metrics block, `Speakable` on the conclusion, site-level `WebSite`/`Organization` — all reading brand config.
- `@astrojs/sitemap` with per-collection chunks; `robots.txt` with sitemap ref + 2026 AI-crawler allow list; `noindex` on 404/utility pages.
- `llms.txt` (copy per SEO §5, brand from config); build-time OG image (Satori/astro-og-canvas): date + closes + bias.
- Prev/next session links on every day page.

**Acceptance**
- [ ] Rich Results Test passes on a fixture day page for all schema types.
- [ ] Sitemap contains only real content routes; OG image renders for a fixture day.
- [ ] Lighthouse still ≥ 95 after all SEO additions (the regression check that matters).
- [ ] Zero new client-side JS shipped.

---

## Phase 7 — Workflows, CI, alerts

**Goal:** the autonomy layer (ORCHESTRATION §1, §6b, §7).

**Deliverables**
- Four workflows: premarket / eod / daily-news crons + `workflow_dispatch` (date + phase inputs).
- Day-type resolver as run entrypoint; start-of-run hygiene (pull, missed-day check, holiday-calendar-expiry check).
- CI: Astro build gate, **premarket-immutability diff on `eod *` commits**, Lighthouse gate.
- ntfy (or Telegram) alerts with the §7 severity table; post-deploy verification + IndexNow ping.

**Acceptance**
- [ ] A test EOD commit that mutates a premarket key **fails CI**.
- [ ] A run killed mid-FETCH produces a `high` alert and commits nothing.
- [ ] `workflow_dispatch` rerun of an already-successful phase results in an empty diff (idempotency proven end-to-end).
- [ ] Resolver: a 2026 NSE holiday date routes to the holiday template; Saturday routes to weekend; both skip metrics/signal.
- [ ] IndexNow ping fires with the correct day URL after a successful deploy.

---

## Phase 8 — Launch & the supervised week

**Goal:** go live without trusting the crons blind.

**Human tasks (Varun — ~45 min once, per SEO §3 / ORCHESTRATION §9)**
- [ ] Domain pointed, one canonical host, other 301s.
- [ ] Secrets set: `OPENROUTER_API_KEY`, alert channel, `INDEXNOW_KEY`, deploy hook.
- [ ] Google Search Console verified + sitemap submitted; Bing Webmaster Tools same (feeds ChatGPT/Copilot — don't skip).
- [ ] Subscribe to the alert topic on phone.

**Supervised week protocol**
- Days 1–2: trigger premarket/EOD **manually** via `workflow_dispatch` at the right times; verify pages, alerts, IndexNow.
- Days 3–5: crons enabled, watch every run land.
- Include one deliberate failure drill: block a primary source, confirm the degraded page publishes + `info` alert fires.
- [ ] SEO.md §9 launch checklist fully green.
- [ ] Five consecutive clean trading-day cycles (both writes) → **the site is autonomous.** Recurring human duties drop to ORCHESTRATION §9's list of three.
