# CLAUDE.md — Standing Rules for the Coding Agent

> Place this at the repo root. It is the first thing Claude Code reads, every session.
> This file is *rules*, not specs. Specs live in: PLANNING.md (site model) · DESIGN.md (visuals) · ORCHESTRATION.md (pipeline) · SEO.md (discoverability) · PHASES.md (build order). When this file and a spec conflict, **stop and ask** — do not pick a side silently.

## What this project is (one line)

A static, date-indexed daily reference for Indian equity markets — Astro + Starlight site, written twice a day by an unattended Python pipeline on GitHub Actions, designed to be fast, honest, and citable by humans and AI.

## Hard rules — never violate, never "improve"

1. **The LLM never touches a number.** All metrics, votes, `bias_score`, labels, conviction come from deterministic code. DeepSeek rewords headlines and writes short prose, nothing else. (ORCHESTRATION §0, §8)
2. **The EOD write never modifies pre-market data.** The sidecar JSON's `premarket` object is read-only after the morning commit; CI enforces this by diff. Never weaken or bypass that check. (ORCHESTRATION §3, §6b)
3. **MDX files are render artifacts.** Never hand-edit, text-append, or patch an MDX. Change the sidecar JSON, re-run the assembler. The assembler must stay deterministic — same JSON in, byte-identical MDX out.
4. **A day page always publishes.** Missing data degrades per the ladder (vote 0 → partial notice → signal suppressed at ≥4 missing → news-only outage page). Never skip a calendar day; never invent a value to fill a gap. (ORCHESTRATION §5b)
5. **No pasted source text, ever.** Reworded headlines + one-line why-it-matters + outbound `source_url` only. A news item without a real URL is invalid. (PLANNING §6)
6. **Brand from config only.** The site name/domain/tagline exist in `src/config/site.ts` and nowhere else — not in components, content, JSON-LD, `llms.txt`, or comments. (PLANNING §11)
7. **Zero client-side JavaScript on content pages.** Everything SEO/rendering is build-time. Pagefind's JS on search interaction is the only exception. No analytics scripts, no islands, no client data fetching. (SEO §6) *Clarified 2026-07-13: Starlight's own native shell JS (mobile ToC drawer toggle, in-page ToC scroll-spy, Astro's link-prefetch) is allowed — it's ~6KB, not analytics/islands/data-fetching, and is what "native Starlight behavior" (PLANNING §2/§3) inherently ships with. The rule targets *added* client JS, not Starlight's own minimal UX scripts.*
8. **Color carries meaning only.** `--up`/`--down` on % changes and votes exclusively; the lavender accent on interaction only. No cards, shadows, or rounded containers — hairlines and whitespace. (DESIGN.md)
9. **The warning banner renders next to every signal display**, including suppressed/degraded states. It is a fixture, not a conditional.
10. **Follow PHASES.md in order.** Don't start a phase before the previous gate passes; don't skip acceptance checks; surface spec contradictions instead of improvising.

## Conventions

- **Pipeline:** Python 3.12, `pipeline/` per ORCHESTRATION §10. Pure functions in `compute/`; side effects only in `fetch/` and `publish` steps. Config-driven thresholds (`data/signal-config.json`) — tuning must never require code edits.
- **Commits:** `premarket YYYY-MM-DD` · `eod YYYY-MM-DD` · `news YYYY-MM-DD` for content; conventional prefixes (`feat:`, `fix:`, `ci:`) for code.
- **Times:** all scheduling logic in IST internally, crons expressed in UTC, all reader-facing timestamps rendered IST with the label.
- **Errors:** fail loudly and early; nothing half-written is ever committed. Every failure path ends in an alert (ORCHESTRATION §7), not a silent log line.
- **Tests:** vote rules, degradation ladder, assembler determinism, and validation gates are unit-tested. If you fix a pipeline bug, add the test that would have caught it.
- **Dependencies:** justify each one. Prefer stdlib/hand-rolled for small things; a maintained library for genuinely gnarly ones (RSS parsing, NSE session handling).

## Definition of done (any task)

Build passes · relevant PHASES.md acceptance boxes check · Lighthouse ≥ 95 unaffected · no hard rule violated · no new recurring human task created (if a change requires one, that's a design smell — redesign it).

## Astro dev server

Start it in background mode: `astro dev --background`. Manage with `astro dev stop`, `astro dev status`, `astro dev logs`. Full docs: https://docs.astro.build (routing, components, framework components, content collections, styling, i18n guides).
