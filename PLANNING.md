# Daily Indian Markets Reference — Planning & Architecture

> **Status:** Planning only. No code in this document. This is a handoff spec for Claude Code.
> **Companion docs:** `DESIGN.md` (visual language) · `SEO.md` (discoverability) · `ORCHESTRATION.md` (scheduling, data-fetch, failure handling) · `PHASES.md` (build order + acceptance gates) · `CLAUDE.md` (agent rules). Read order in `README.md`.
> **Working domain:** `niftyfiftyone.com` (temporary — see [Brand as a variable](#brand-as-a-variable); do not hardcode the name).
> **Framework:** Astro + Starlight (docs shell), static output.
> **Content author:** an autonomous AI agent (DeepSeek via OpenRouter) writes one file per day. No manual editing.

---

## 1. What this site is

A **daily, date-indexed reference archive** of the Indian equity market. Its job: when someone (a person *or* an AI agent) wants to know *what happened in the market on a given day and which news drove it*, this site is the fast, clean, citable answer — with **direct outbound links to the original news sources** rather than rehosted article text.

It is a "reference machine," not a blog to be read cover to cover. The primary access pattern is **by date**. (Stock-axis lookup — "everything about Reliance over time" — is explicitly out of scope for v1.)

### The three jobs, in priority order
1. **Date lookup** — "take me to July 11" → a complete, scannable day page.
2. **SEO surface** — rank for "nifty today", "why did sensex fall today", "market outlook [date]".
3. **AI-citability** — be the source an LLM quotes when asked "what happened to Indian markets on [date]". This shapes structured data and `llms.txt` (Section 8).

---

## 2. The daily page model

**One URL per calendar day.** Written **twice** on trading days, appended in place:

```
/2026/07/11/
```

### Trading-day page = two stacked sections

**Section 1 — Pre-Market (written before/at open ~9:00 IST)**
- All markets data (global cues, prev-day domestic close, FII/DII, VIX, USD-INR…)
- Important pre-market news (top items, each with outbound link)
- Market expectations (plain-English read of the setup)
- **Accumulated Long / Short signal** + the warning banner (Section 5)

**Section 2 — EOD / Close (appended after close ~4:00 IST)**
- How the market actually performed today (index closes, %, breadth)
- Top-10 news that moved the market, each with outbound link
- Short conclusion / synthesis

**Critical rule for the agent:** the EOD write **appends below** the Pre-Market section. It **never deletes or rewrites** the morning content. *(Mechanically enforced via the sidecar-JSON model + CI immutability check — ORCHESTRATION.md §3 and §6b. The MDX is a render artifact, never text-appended.)* The morning Long/Short call stays permanently visible above the outcome — this open-vs-close accountability is the site's credibility edge and later feeds signal-accuracy tracking.

### Weekend page = news-only
Saturday & Sunday: markets are closed, so **no bias engine, no open/close split.** Just the day's market-relevant general news with outbound links. This is a distinct, simpler template.

**NSE holidays use the same template**, with the closure reason rendered ("Markets closed — Republic Day"). Day-type resolution (trading / weekend / holiday) and the committed holiday-calendar file are specced in ORCHESTRATION.md §2.

### Right-rail "On this page" nav
Auto-generated from headings. On a trading day it resolves to two primary anchors — **Pre-Market** and **EOD** — optionally with sub-anchors (Markets Data / News / Signal under each). This is exactly Starlight's native table-of-contents behavior; no custom work.

---

## 3. Information architecture & URL scheme

```
/                         → homepage: latest day rendered in full + compact "recent days" rail
/2026/                    → year index (months)
/2026/07/                 → month index (days, reverse-chron)
/2026/07/11/              → a single day (the core page)
/about/                   → what this is, methodology, disclaimer
/llms.txt                 → machine-readable index for AI crawlers (Section 8)
/sitemap-index.xml        → auto (Astro sitemap)
```

- **Left sidebar:** year → month → day tree, with counts. Reverse-chronological (newest on top). Native Starlight sidebar, generated from the content collection.
- **Center:** the day page.
- **Right:** on-this-page ToC.
- **Top:** Pagefind search (offline, free, indexes rendered text).

**URL determinism:** the agent computes the path from the date alone (`/YYYY/MM/DD/`). It never needs to read site state to know where a file goes. File name mirrors it: `src/content/docs/YYYY/MM/DD.mdx`.

---

## 4. Content schemas (frontmatter)

Two Zod-validated content-collection schemas. Validation is a **feature**: a malformed agent write fails the build loudly instead of publishing garbage. The agent's contract is "produce valid frontmatter + fill the section bodies."

### 4a. Trading-day schema (fields, not code)

**Identity**
- `date` (ISO, required) · `type: "trading-day"` · `title` (auto: "Nifty & Sensex — 11 Jul 2026")

**Pre-Market metrics block** — a fixed, always-present key set so both the agent and machine-readers can rely on it. Each numeric metric also carries a derived signal vote (see Section 5):
- `gift_nifty` (value, Δ% vs prev close, vote)
- `sp500_overnight` (Δ%, vote)
- `nasdaq_overnight` (Δ%, vote)
- `us10y_yield` (level, Δ, vote)
- `dxy` (level, Δ, vote)
- `brent` (value, Δ, note — context flag, not a directional vote)
- `fii_net_cash` (₹ cr, prev day, vote)
- `dii_net_cash` (₹ cr, prev day, vote)
- `india_vix` (level, Δ, **conviction dampener** flag — not a direction vote)
- `usdinr` (value, Δ, vote)
- `prev_close_in_range` (where prev close sat in its day range, vote)

**Derived signal**
- `bias_score` (integer net of the votes) · `bias_label` ("Long" / "Short" / "Neutral" / "Cautious") · `conviction` (damped when VIX spikes)

**Pre-market news** — array; each item: `headline_reworded`, `why_it_matters` (1 line), `source_name`, `source_url`, `timestamp`. **No field ever holds pasted article text** (copyright + duplicate-content SEO poison). Reworded headline only.

**EOD block** (filled on the second write)
- `nifty_close`, `sensex_close`, `banknifty_close` (each: value, Δ%)
- `advance_decline`, `sector_leaders`, `sector_laggards`
- `eod_news`: array of up to 10, same shape as pre-market news
- `conclusion` (short synthesis)
- `eod_written: true` (flips when the close write lands; drives "awaiting EOD" state)

### 4b. Weekend schema
- `date` · `type: "weekend"` · `title`
- `news`: array of items (same news shape). No metrics, no signal, no EOD.

---

## 5. The Long / Short signal

The signal is the site's signature feature and its main AI-citable artifact. It is the LeanSide pre-market bias engine, surfaced publicly.

**Mechanics (already designed in your LeanSide work):** each input casts a weighted **−1 / 0 / +1** vote per the rules you specified (GIFT Nifty vs prev close ±0.3% thresholds, S&P/Nasdaq overnight, US10Y falling = mild +, rising DXY = − for India, FII/DII net, USD-INR weakening = −, prev close in top third = + momentum). **India VIX and Brent are treated separately** — VIX rising sharply *dampens conviction* rather than setting direction; Brent is a context note. Votes sum to `bias_score`; `bias_label` is derived from the net; `conviction` is reduced on VIX spikes.

**Display (visible, transparent — not advice):**
- A compact **signal table**: `Input | Value | Vote (−1/0/+1)` — full transparency, this is what an AI cites.
- A **net readout**: e.g. "Bias: **Mildly Long** · +4 · conviction reduced (VIX elevated)".

**Mandatory warning banner**, adjacent to every signal display, in plain language:
> *This is not financial advice. The Long/Short signal is an automated guess derived only from publicly available market data. It is frequently wrong, especially about where the market closes. Do your own research.*

**Honesty note carried from LeanSide:** these signals predict *open* direction better than *close* direction (~52–56%). The morning call being preserved next to the EOD outcome makes that visible rather than hidden — a feature, not a bug.

---

## 6. Where the data comes from

Two independent pipelines feed each day. Both are the agent's responsibility; the site itself only renders files.

- **News → RSS.** Moneycontrol, ET Markets, Livemint, Business Standard feeds. Clean and legal. Agent selects, **rewords headlines into its own words**, writes a one-line "why it matters", keeps the **outbound link + timestamp**. Never stores article body text.
- **Metrics → data-fetch layer.** FII/DII, VIX, index levels, GIFT Nifty aren't in RSS. Sources per your signal table: NSE / Moneycontrol (FII/DII, VIX, breadth), Yahoo Finance (S&P, Nasdaq, DXY, USD-INR, Brent, US10Y), FRED (yields). This fetch layer is its own component in the build; spec it separately when we move to execution.

**Legality/SEO posture:** the site is a **citation hub** — outbound links to originals, original reworded summaries only. This is exactly what both Google (no duplicate content) and AI crawlers (clean, attributed, structured) reward.

---

## 7. The agent write-contract (daily, unattended)

The agent's job ends at "write a valid file + commit + push." A push triggers a static rebuild (Netlify/Vercel/Cloudflare). No database, no API, no auth for the agent to manage.

**Trading day**
1. **~09:00 IST** — fetch metrics + pre-market RSS → compute votes + `bias_score` → write `src/content/docs/YYYY/MM/DD.mdx` with the Pre-Market section and `eod_written: false`. Commit "premarket YYYY-MM-DD". Push.
2. **~16:00 IST** — fetch close data + top-10 EOD news → **append** the EOD block, set `eod_written: true`. Commit "eod YYYY-MM-DD". Push. **Morning section untouched.**

**Weekend**
- One write: fetch general market news → weekend template. Commit. Push.

**Guardrails (belong in the agent spec, enforced by schema + rules):**
- Schema validation gates the build — malformed → build fails → nothing publishes.
- Every news item must carry a real `source_url`; no item without a link.
- No field may contain pasted source text; reworded summaries only.
- EOD write must not modify pre-market fields (structural separation makes this checkable).

---

## 8. SEO & AI-citability layer

**On-page SEO**
- Fast static pages, no images by default (light, quick, crawlable — matches the design intent).
- Per-page `<title>`/meta tuned to the **two intents**: pre-market ("Nifty outlook — 11 Jul") and EOD ("How markets closed — 11 Jul"). Both live on one URL; the meta leads with the freshest.
- Homepage always shows the **latest day in full** above the fold → fresh indexable content daily.
- Auto sitemap (Astro integration). Clean internal linking via the date tree.

**Structured data (JSON-LD)** on each day page:
- `Article` / `NewsArticle` (datePublished, dateModified — the two writes make `dateModified` meaningful), `headline`, `about`.
- Consider `Dataset` semantics for the metrics block so the numbers are machine-parseable.
- Mark outbound news links with clear citation semantics.

**AI-native**
- **`llms.txt`** at root: a machine-readable index — what the site is, URL pattern (`/YYYY/MM/DD/`), what each day contains, the signal's meaning and its explicit "guess, not advice" caveat. This is how an agent learns to navigate and cite you.
- Because content is structured (fixed metric keys, reworded headlines + links, a labeled signal), an LLM can extract "on 11 Jul: Nifty closed −0.8%, FII net sold ₹X cr, bias was Mildly Long, top driver was [reworded headline] → [link]" cleanly. That extractability *is* the product.

---

## 9. Search

- **Pagefind** (Starlight default): offline, free, full-text over rendered pages. Handles "find the day X was mentioned" well.
- **Limitation to accept for v1:** Pagefind is full-text, not structured query. "Show all days FII net sell > ₹5000 cr" is **not** a v1 feature — that's a SQLite/API job for a later version. v1 is a reference archive, not a query engine.

---

## 10. Visual language

Full detail in the companion **`DESIGN.md`**. Summary:
- **Dark canvas**, near-black (not pure #000), off-white text, muted grey secondary.
- **Structure by hairline rules**, never cards or shadows (the getdesign.md pattern) — whitespace + 1px lines.
- **Type:** Source Serif 4 (headings, warm/editorial), Geist Sans (body), Geist Mono (all numbers, tabular figures). All free, self-hostable.
- **Monochrome base; color only carries meaning** — red/green reserved strictly for % changes and the Long/Short signal. One calm accent for links/active-nav.
- **No images.** Text + rules only. Light, fast, calm — "quiet reference", not "dev tool", not "trading terminal".

---

## 11. Brand as a variable

`niftyfiftyone.com` is the **current, temporary** identity. To make a future rebrand a one-line change, not a site-wide find-and-replace:
- Store site name, domain, and tagline in **one config** (`src/config/site.ts` or Astro/Starlight site config).
- Every template, meta tag, `llms.txt`, and JSON-LD field reads from that config — **never** a hardcoded string.
- Content files (the daily `.mdx`) contain **no brand references** — they're pure data + prose, so they survive a rename untouched.

---

## 12. Scope boundaries (v1)

**In:** date-indexed daily pages, two-section trading days, weekend news pages, fixed metrics block, visible Long/Short signal with warning, top-10 EOD news with outbound links, Pagefind search, docs-style three-column layout, dark/hairline/Geist+Serif skin, SEO + `llms.txt` + JSON-LD, agent write-contract, brand-as-config.

**Out (later versions):** stock-axis pages, structured metric queries, SQLite/API backend, signal-accuracy dashboard, historical backfill, any manual editing workflow.

---

## 13. Open items — resolved

1. **Data-fetch layer** — ✅ specced in ORCHESTRATION.md §5 (source table with fallbacks, retry policy, missing-data degradation ladder).
2. **`DESIGN.md`** — ✅ delivered, including the awaiting-EOD / degraded / holiday page states.
3. **JSON-LD field mapping + `llms.txt` copy** — drafted during PHASES.md Phase 6 (SEO wiring), per SEO.md §4–5.
4. **Deploy target** — human decision, ORCHESTRATION.md §12 (Cloudflare Pages recommended). Any git-push-rebuild host satisfies the spec.
5. **Weekend/holiday distinction, NSE holiday calendar, scheduling, alerting, recovery** — ORCHESTRATION.md §1–§2, §7.
