# ORCHESTRATION.md — How the Site Runs Itself

> Fourth handoff doc, alongside PLANNING.md, DESIGN.md, SEO.md. This one answers the question the others leave open: **who runs the agent, when, and what happens when something breaks.**
> Everything here is spec, no code. Claude Code implements against it.
> **Brand is a variable** — nothing here references the brand name; the pipeline is brand-agnostic (PLANNING §11).

---

## 0. The one principle everything hangs on

> **Deterministic spine, LLM at the edges.**

The pipeline is ordinary Python: fetch numbers, compute votes, assemble files, validate, commit. The LLM (DeepSeek via OpenRouter) is called for exactly two things — **rewording headlines** and **writing short prose** (why-it-matters lines, market expectations, EOD conclusion). 

**The LLM never sees, produces, or transforms a number.** Every metric, vote, `bias_score`, `bias_label`, and conviction flag is computed by deterministic code from fetched data. If the LLM hallucinates, the worst case is an awkward sentence — never a wrong Nifty close. On a site whose entire value proposition is citability, this is the load-bearing rule.

---

## 1. Where it runs — GitHub Actions

**Decision: GitHub Actions scheduled workflows, in the same repo as the site.**

Why this over the alternatives:

| Option | Verdict |
|---|---|
| **GitHub Actions cron** | ✅ Pipeline + content + site in one repo. No server to maintain. Free at this volume (~15 min/day of runner time). Secrets management built in. Push from the workflow *is* the deploy trigger. |
| Mac + launchd (LeanSide-style) | ❌ A public site cannot depend on a laptop being awake at 8:30 AM. |
| DigitalOcean VPS cron | Workable, precise timing — but adds a server to patch, a deploy key to manage, and a second place where things break. Keep as fallback if Actions cron drift ever becomes a real problem. |

**Known caveat: cron drift.** GitHub Actions schedules can start up to ~15 minutes late at peak. The schedule below builds in buffer so drift never matters.

### Schedule (all crons in UTC; IST = UTC+5:30)

| Run | Cron (UTC) | Lands (IST, with drift) | Day filter |
|---|---|---|---|
| **Pre-Market** | `45 2 * * 1-5` | 08:15–08:35 | trading days only (see §2) |
| **EOD** | `45 10 * * 1-5` | 16:15–16:35 | trading days only |
| **Weekend / Holiday** | `30 5 * * *` | 11:00–11:20 | runs daily; exits unless today is a weekend or NSE holiday |
| **Manual** | `workflow_dispatch` | on demand | takes `date` + `phase` (premarket / eod / news) inputs for reruns and backfills |

Pre-market at ~08:40 IST is deliberate: FII/DII provisional numbers for the previous day are published the prior evening, GIFT Nifty and US closes are long settled, and NSE pre-open doesn't start until 09:00. Nothing is gained by running later, and the buffer absorbs drift.

The weekday crons also fire on NSE holidays — the **day-type resolver** (§2) is what decides which template actually gets written. Every run starts with it.

---

## 2. Day-type resolver

First step of every run. Three outcomes:

```
resolve(date) → "trading" | "weekend" | "holiday"
```

- **Weekend:** Saturday/Sunday → weekend template (news-only, PLANNING §2).
- **Holiday:** date appears in `data/nse-holidays-YYYY.json` → weekend-style template, with the holiday name rendered as the reason ("Markets closed — Republic Day"). Same schema as weekend (`type: "holiday"` or reuse `"weekend"` with a `reason` field — implementer's choice, but the reason must render).
- **Trading:** everything else → the two-write day.

**The holiday calendar is a committed static file**, one per year, sourced from NSE's published holiday list. Updating it is a once-a-year, two-minute manual task (add it to the §9 checklist). If today's date is past the last date covered by any holiday file, the run **alerts** (§7) — "holiday calendar expired" — rather than guessing.

**Muhurat trading** (one evening session around Diwali): treat the day as a holiday page with a one-line note. Do not attempt a special pipeline for a one-hour session — out of scope, same as v1's other exclusions.

---

## 3. The sidecar JSON — source of truth per day

This is the structural fix that makes "EOD appends, never rewrites" **enforceable** instead of aspirational.

```
data/days/2026-07-11.json     ← source of truth (agent writes this)
src/content/docs/2026/07/11.mdx  ← deterministically ASSEMBLED from the JSON
```

- **Pre-market run:** writes the JSON with the `premarket` block populated and `eod: null`. Then assembles the MDX from it. Commits both.
- **EOD run:** reads the committed JSON, adds the `eod` block, **does not touch a single key inside `premarket`**, re-assembles the MDX from the merged JSON. Commits both.
- The MDX is a *render artifact*. It is never edited in place, never appended to as text. If the assembler is deterministic (it must be — stable key order, no timestamps-of-generation inside content), then re-running assembly on unchanged data produces a byte-identical file.

**Why this matters:**
1. **Immutability becomes machine-checkable.** CI diffs the `premarket` object between the two commits of the day; any change fails the build (§6).
2. **Idempotency for free.** A crashed or duplicate run re-fetches, re-assembles, and produces the same output — safe to rerun any phase, any time.
3. **Future-you gets structured history.** The `data/days/` directory *is* the future SQLite import, signal-accuracy dashboard feed, and API — without having designed any of them yet.

---

## 4. Pipeline stages

Every run is the same six stages. Failure at any stage → alert (§7); stages 1–3 have retries.

```
FETCH → COMPUTE → COMPOSE → ASSEMBLE → VALIDATE → PUBLISH
```

### Pre-market run (trading day, ~08:40 IST)
1. **FETCH** — metrics from the source table (§5) + pre-market items from the RSS set. Per-source: 3 attempts, exponential backoff (5s/15s/45s), then fallback source, then mark missing.
2. **COMPUTE** — deterministic: votes per the LeanSide rules (PLANNING §5), `bias_score`, `bias_label`, conviction damping from VIX. Missing-input policy per §5b below.
3. **COMPOSE** (LLM) — one structured call: input = selected RSS items (title, source, url, timestamp) + the computed setup; output = strict JSON: reworded headlines, why-it-matters lines, "market expectations" paragraph. Contract in §8.
4. **ASSEMBLE** — write sidecar JSON, render MDX from it.
5. **VALIDATE** — local: Zod schema pass, every news item has a `source_url`, no URL appears in prose that isn't in a news item, reworded headline ≠ verbatim original (cheap similarity check).
6. **PUBLISH** — commit `premarket YYYY-MM-DD`, push. Deploy is triggered by the push. Post-deploy verification per §6c.

### EOD run (trading day, ~16:20 IST)
Same stages; FETCH = index closes, breadth, sector moves + EOD RSS sweep; COMPOSE = top-10 reworded news + conclusion paragraph; ASSEMBLE = merge into existing JSON (**premarket block read-only**), set `eod_written: true`; commit `eod YYYY-MM-DD`.

### Weekend / holiday run (~11:00 IST)
FETCH = RSS only → COMPOSE = reworded items → ASSEMBLE → VALIDATE → PUBLISH. No metrics, no signal, no second write.

### Start-of-run hygiene (every run)
- `git pull` first (never build on stale state).
- **Missed-run check:** scan the last 7 calendar days (weekends included — a weekend page is expected content) for archive gaps; any missing day → one aggregated alert with severity `missed-day`. Days before the archive's first sidecar are pre-launch, not gaps. *(Amended 2026-07-17: the original check looked only at yesterday and skipped weekends, which let a missing Sunday page go unnoticed.)*
- **Recovery for a missed day** is manual, and never reconstructs data. If the day is recent enough to run live (same day, via `workflow_dispatch` — see §7), do that. If the window to capture live data has passed, the sanctioned recovery is a **hand-written outage sidecar**: every metric marked unavailable, `data_quality: "outage"`, signal suppressed, empty news, and prose that states plainly the pipeline did not run — nothing invented, nothing back-dated as if live. (`eod_missed: true` similarly converts a forever-"awaiting EOD" page into an honest "EOD not captured" note.) This keeps CLAUDE.md rule 4's "never skip a calendar day" satisfied without violating the no-reconstruction principle — an outage page doesn't pretend to be a live one. *(Decision 2026-07-17, applied to 2026-07-10/12/15 and 07-14's missing EOD.)*

---

## 5. Data-fetch layer

### 5a. Source table — primary and fallback per metric

| Metric | Primary | Fallback | Notes |
|---|---|---|---|
| GIFT Nifty | Yahoo Finance (`GIFT NIFTY` future) | Moneycontrol page value | vs prev Nifty close, ±0.3% thresholds |
| S&P 500 / Nasdaq overnight | Yahoo Finance (`^GSPC`, `^IXIC`) | Stooq | prior US close Δ% |
| US 10Y yield | FRED | Yahoo (`^TNX`) | level + Δ |
| DXY | Yahoo (`DX-Y.NYB`) | Stooq | level + Δ |
| Brent | Yahoo (`BZ=F`) | — | context note only, no vote |
| USD/INR | Yahoo (`INR=X`) | — | Δ direction |
| FII / DII net cash | NSE published provisional (prev day) | Moneycontrol FII/DII page | ₹ cr |
| India VIX | NSE | Moneycontrol | conviction dampener, no direction vote |
| Prev close position in range | computed from prev day's own stored JSON | Yahoo OHLC | this is why the sidecar archive pays off immediately |
| Index closes / breadth / sectors (EOD) | NSE | Moneycontrol | EOD run only |

Implementation note for Claude Code: NSE endpoints are cookie/header-fussy — the fetcher needs a browser-like session and must treat NSE as the *most likely* source to fail, hence every NSE metric has a fallback.

**News RSS set:** Moneycontrol, ET Markets, Livemint, Business Standard (per PLANNING §6). A feed that errors is skipped with a warning, not fatal — news selection works from whatever feeds responded, minimum one.

### 5b. Missing-data policy (the degradation ladder)

The hard rule: **a day page always publishes.** A degraded page with honest "unavailable" markers beats a hole in a date-indexed archive, every time.

1. **One directional input missing** → its vote = `0`, value rendered as `—` with a muted "unavailable" note in the signal table. `data_quality: "partial"` in frontmatter; a quiet one-line notice renders near the signal ("2 of 11 inputs unavailable this morning").
2. **VIX missing** → conviction damping skipped, noted.
3. **≥ 4 directional inputs missing** → signal suppressed for the day: no `bias_label`, table shows what was fetched, notice explains ("insufficient data for a signal this morning"). Never publish a bias computed from a minority of inputs — a confidently wrong signal is worse than an honest gap.
4. **All metrics failed** (network catastrophe) → publish news-only for the day with a data-outage notice, `data_quality: "outage"`. Alert severity `high`.
5. **RSS entirely failed** → publish metrics + signal without news, notice shown. (Both failing → the run genuinely fails → alert `high`, manual rerun.)

Every degradation is stored in the sidecar JSON (`missing: [...]`), so degraded days are queryable later.

---

## 6. Validation gates — three layers

**a. Local (in the run, before commit)** — Zod schema on frontmatter; every news item has `source_url`; reworded-headline similarity check; LLM output parsed as strict JSON (§8). Fail → the run fails *before* anything is committed. Nothing half-written ever reaches the repo.

**b. CI (on push, before deploy)**
- Full Astro build (schema violations fail loudly — PLANNING §4's "validation is a feature").
- **Immutability check:** on any `eod *` commit, diff today's sidecar `premarket` object against the previous commit. Any change → fail. This is the mechanical enforcement of the site's credibility rule.
- Lighthouse/CWV gate ≥ 95 (SEO.md §6) — on a sampled page, not the whole site.

**c. Post-deploy (end of run)**
- Poll the live day URL (up to ~3 min): expect HTTP 200 and today's date string in the body; after the EOD run, additionally expect the EOD heading. Fail → alert `high` ("committed but not live").
- **IndexNow ping** for the day's URL on success (SEO.md §3.4) — this is where "publish twice daily" turns into "indexed within minutes."

---

## 7. Alerting & recovery

**Channel: ntfy.sh** (or a Telegram bot — pick one, it's a single `curl` either way; ntfy needs zero account setup). Subscribe on the phone once.

| Severity | Fires when | Example |
|---|---|---|
| `info` | successful run with degradation | "premarket published — 2 inputs missing (DXY, US10Y)" |
| `high` | run failed; page not published or not live | "EOD run failed at FETCH: NSE unreachable after retries" |
| `missed-day` | start-of-run check finds a gap | "no page exists for 2026-07-10" |
| `config` | maintenance needed | "holiday calendar expires in 14 days" |

**Silence = success.** No daily "everything worked" noise, or the alerts get ignored within a week.

**Recovery is manual by design (v1):** every failure is fixed by re-running `workflow_dispatch` with `date` + `phase`. Because runs are idempotent (§3), reruns are always safe — including re-running a phase that already succeeded. That single property removes the need for any bespoke recovery logic.

**Rollback:** a bad publish is `git revert` + push. The sidecar model means reverting the commit reverts both data and page coherently.

---

## 8. The LLM contract (COMPOSE stage)

- **Model:** DeepSeek via OpenRouter (per PLANNING). Temperature low (~0.3) — this is editorial rewording, not creativity.
- **Input:** raw RSS items (original title, source, URL, timestamp) + the computed setup summary (as *rendered text*, for context only).
- **Output: strict JSON only** — no markdown fences, no preamble. Parsed and schema-checked; a parse failure retries the call up to 2× with the error appended, then the run fails validation (nothing publishes malformed).
- **Per-item output:** `headline_reworded`, `why_it_matters` (≤ 1 sentence), plus passthrough of `source_name`, `source_url`, `timestamp` — the pipeline copies the passthrough fields from *its own* input, never trusting the LLM to echo URLs correctly.
- **Hard bans, enforced by validation not politeness:** no numbers in prose that don't appear in the fetched metrics (regex-scan prose for numerals and cross-check); no verbatim source sentences (similarity check); no URLs in prose.
- **Prose fields:** "market expectations" (pre-market) and "conclusion" (EOD) — each ≤ ~120 words, first sentence = the answer (SEO.md §7 rule 1).
- **Cost reality:** two small calls per trading day + one per weekend day ≈ well under **$1/month** at DeepSeek pricing. Cost is a non-issue; don't engineer around it.

---

## 9. Config, secrets, and the human's standing duties

**Secrets (GitHub Actions secrets):** `OPENROUTER_API_KEY`, `NTFY_TOPIC` (or Telegram token/chat-id), `INDEXNOW_KEY`, deploy hook URL if the host needs one.

**Committed config:** brand config (PLANNING §11) · `data/nse-holidays-YYYY.json` · vote thresholds/weights in one `signal-config` file (so tuning the engine never means editing pipeline code).

**The complete list of recurring human tasks** (everything else is autonomous):
1. **Yearly (~Dec):** add next year's NSE holiday file. The `config` alert nags if forgotten.
2. **Weekly, 10 min:** Search Console glance (SEO.md §3.5).
3. **On alert:** rerun via `workflow_dispatch`, or fix and revert.

If a fourth recurring task appears during implementation, that's a design smell — push it back into the pipeline.

---

## 10. Repo layout (orchestration view)

```
.github/workflows/
  premarket.yml · eod.yml · daily-news.yml · manual.yml (workflow_dispatch)
pipeline/                    # Python; shared stages, thin entrypoints per phase
  fetch/  compute/  compose/  assemble/  validate/
data/
  days/YYYY-MM-DD.json       # sidecar source of truth (§3)
  nse-holidays-2026.json
  signal-config.json
src/                         # Astro + Starlight site (PLANNING/DESIGN)
  content/docs/YYYY/MM/DD.mdx   # render artifacts — never hand-edited
```

---

## 11. Build order for Claude Code (with acceptance criteria)

1. **Site shell first** (Astro + Starlight + DESIGN.md skin) rendering from 3–4 *hand-written* sidecar JSON fixtures — one full trading day, one awaiting-EOD day, one weekend, one degraded day. ✅ *Accept:* all four states render correctly, including the "EOD update expected ~4:15 PM IST" placeholder and the degraded-data notice.
2. **Assembler + schemas.** JSON → MDX deterministic. ✅ *Accept:* running the assembler twice on the same JSON yields byte-identical MDX; invalid JSON fails the build.
3. **Fetch layer** with the §5 source table. ✅ *Accept:* a forced primary-source failure exercises fallback → missing-marker path; output JSON records `missing`.
4. **Compute layer** from `signal-config`. ✅ *Accept:* unit tests for every vote rule + the degradation ladder (esp. the ≥4-missing suppression).
5. **Compose (LLM) + validation gates.** ✅ *Accept:* malformed LLM JSON never reaches a commit; number-in-prose and similarity checks demonstrably catch violations.
6. **Workflows + alerts + immutability CI check.** ✅ *Accept:* a test EOD commit that mutates a premarket key fails CI; a killed run produces an ntfy alert; `workflow_dispatch` rerun of a completed phase is a no-op diff.
7. **Post-deploy verification + IndexNow.** ✅ *Accept:* deploy of a new day pings IndexNow with the correct URL.

Run **one full week supervised** (manual triggers, watching alerts) before trusting the crons — that week is the real acceptance test.

---

## 12. Open decisions (Varun, before execution)

1. **Deploy host** — Netlify / Vercel / Cloudflare Pages (all fine; Cloudflare Pages is the cheapest at scale and pairs well with the static-only posture).
2. **Alert channel** — ntfy.sh (zero setup) vs Telegram bot (you already live in Telegram-adjacent workflows).
3. **Trailing-slash canonical form** — pick once (SEO.md §2.1); Astro's default is trailing slash, keep it.
4. Confirm the LeanSide vote thresholds transfer as-is into `signal-config.json`, or whether the public site should run a slightly more conservative labeling ("Mildly Long" starting at a higher |score|) than your private engine.
