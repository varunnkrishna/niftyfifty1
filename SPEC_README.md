# niftyfiftyone — Handoff Package

Six documents. Together they are the complete, self-contained spec for building and running the site. Drop all six into the new repo root before the first Claude Code session.

## The documents and what each owns

| File | Owns | One line |
|---|---|---|
| **CLAUDE.md** | Standing rules | The 10 hard rules + conventions the agent re-reads every session. Lives at repo root permanently. |
| **PLANNING.md** | Site model | What the site is: daily two-write pages, URL scheme, schemas, signal, scope boundaries. |
| **DESIGN.md** | Visual language | Colors, type, hairline structure, layout, the signal readout, all page states. |
| **ORCHESTRATION.md** | Autonomy | Scheduling (GitHub Actions), day-type resolver, sidecar JSON, data-fetch layer, failure ladder, LLM contract, alerts, recovery. |
| **SEO.md** | Discoverability | Build-time SEO, JSON-LD, `llms.txt`, AI-crawler posture, your one-time account setup. |
| **PHASES.md** | Build order | Phases 0–8 with acceptance gates. The agent's execution track. |

**Reading order for the agent:** CLAUDE.md → PLANNING.md → DESIGN.md → ORCHESTRATION.md → SEO.md → PHASES.md, then execute PHASES.md from Phase 0.

## Kickoff prompt (copy-paste to Claude Code)

> Read CLAUDE.md, then PLANNING.md, DESIGN.md, ORCHESTRATION.md, SEO.md, and PHASES.md in full before writing any code. Confirm your understanding of the 10 hard rules in CLAUDE.md, then begin PHASES.md Phase 0. Work strictly phase by phase; do not start a phase until every acceptance box of the previous one checks. Phase 1 ends with a human review gate — stop there and show me all five fixture page states. If any two documents contradict each other, stop and ask me instead of choosing.

## Decisions you must make first (5 minutes)

From ORCHESTRATION.md §12 — the agent will ask if you don't pre-answer:

1. **Deploy host:** Netlify / Vercel / **Cloudflare Pages (recommended)**.
2. **Alert channel:** ntfy.sh (zero setup) or Telegram bot.
3. **Canonical URL form:** keep Astro's trailing-slash default (recommended) — just confirm.
4. **Public signal thresholds:** copy LeanSide's as-is, or set more conservative public labels.

## Your setup tasks (once, ~45 min — nothing here is coding)

Detailed in SEO.md §3 and PHASES.md Phase 8: domain + canonical host → GitHub secrets (`OPENROUTER_API_KEY`, alert topic, `INDEXNOW_KEY`, deploy hook) → Google Search Console → Bing Webmaster Tools (feeds ChatGPT/Copilot — do not skip) → subscribe to alerts on your phone.

## After launch, your total recurring workload

Three items (ORCHESTRATION.md §9): yearly NSE holiday file, a 10-minute weekly Search Console glance, and acting on alerts via `workflow_dispatch` reruns. If anything else becomes recurring, the pipeline has a design bug — fix the pipeline, not the habit.
