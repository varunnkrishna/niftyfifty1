# DESIGN.md — Daily Indian Markets Reference

> A reusable design reference for the coding agent. Colors, type, spacing, structure, and the reasoning behind them, so every page follows one visual language.
> **Brand name is a variable** (currently "niftyfiftyone") — never hardcode it into styles or components. See PLANNING.md §11.

---

## Design thesis

A **quiet reference**, not a trading terminal and not a dev tool. The page should feel calm, trustworthy, and human — a well-set document you consult, not a dashboard that shouts. Warmth comes from the serif headings; rigor comes from hairline structure and monospace numbers. The market's red/green is the *only* saturated color on the page, so it carries meaning instead of decoration.

Two references were deliberately combined:
- **Structure** from a docs shell (three columns: date tree · content · on-this-page).
- **Skin** from a dark, hairline-ruled directory aesthetic — whitespace and 1px lines do all the structural work; no cards, no shadows.

---

## Color

Dark canvas. Near-black, never pure `#000`. Monochrome base; color only where it means something.

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#0E0E10` | Page canvas (slightly lifted off true black) |
| `--surface` | `#161618` | Rare raised zone (search field, active nav row) — used sparingly, prefer rules over fills |
| `--rule` | `#26262A` | Hairlines — the primary structural device |
| `--text` | `#EDEDEA` | Primary text (off-white, warm, not #FFF) |
| `--text-muted` | `#9A9AA2` | Secondary text, labels, timestamps |
| `--accent` | `#8B8BF5` | Links, active nav, focus — one calm lavender, low saturation |
| `--up` | `#4ADE80` | Positive % change, Long vote (+1) — **meaning only** |
| `--down` | `#F87171` | Negative % change, Short vote (−1) — **meaning only** |
| `--flat` | `#9A9AA2` | Zero vote / unchanged (same as muted) |

**Rules for color**
- Red/green appear **only** on numeric % changes and on signal votes. Never on borders, headings, backgrounds, or decoration.
- The lavender accent is for interaction (links/active/focus) only — not for emphasis in prose.
- Everything else is on the greyscale ramp. If a color isn't carrying meaning, it shouldn't be saturated.

---

## Typography

Three roles, three families. All free, SIL/OFL-licensed, self-hosted (no runtime font logic for the agent).

| Role | Family | Notes |
|---|---|---|
| **Display / headings** | **Source Serif 4** | Warm, editorial, trustworthy. The page's personality. Weights 400/600. |
| **Body / UI** | **Geist Sans** | Clean modern grotesk, not Inter. Reading text, nav, labels. |
| **Numbers / data** | **Geist Mono** | **Tabular figures** — metric columns must align. All prices, %, ₹ cr, votes. |

**Why this pairing:** the serif on top gives a human, credible voice (the opposite of a cold quant terminal); Geist Sans + Geist Mono share a superfamily, so body and data share proportions and the numeric columns line up perfectly. Boldness is spent in exactly one place — the serif headings — and everything else stays disciplined.

**Type scale** (major-third-ish, tightened for density):

| Token | Size / line-height | Family | Use |
|---|---|---|---|
| `display` | 34 / 1.15 | Source Serif 4 600 | Day page H1 ("Nifty & Sensex — 11 Jul 2026") |
| `h2` | 24 / 1.2 | Source Serif 4 600 | Section heads (Pre-Market, EOD) |
| `h3` | 18 / 1.3 | Source Serif 4 600 | Sub-heads (Markets Data, News) |
| `body` | 16 / 1.6 | Geist Sans 400 | Prose, news summaries |
| `label` | 12 / 1.2 | Geist Mono 500, uppercase, +0.08em tracking | Eyebrows, metric labels, table headers |
| `data` | 15 / 1.4 | Geist Mono 500, tabular-nums | Metric values, % changes, votes |

**Smart quotes on**, sentence case for UI, tabular figures wherever numbers stack.

---

## Structure — the hairline system

Structure is carried by **1px rules on the `--rule` token and whitespace**. No cards, no border-radius on containers, no shadows.

- **Section dividers:** a full-width hairline above each major section (Pre-Market, EOD).
- **Table rows:** each metric/news row separated by a bottom hairline. No zebra striping, no cell borders.
- **Column split:** the three-column shell separated by vertical hairlines where two columns meet (as in the reference).
- **Eyebrows:** each section opens with a Geist Mono uppercase label (e.g. `PRE-MARKET · 09:05 IST`) above the serif heading. The eyebrow encodes *real information* (phase + timestamp), not decoration.

**Spacing:** generous. Base unit 8px. Section vertical rhythm 48–64px. Row padding 12–14px vertical. Let the page breathe — density comes from alignment, not cramming.

---

## Layout

Three-column docs shell (Starlight-native), no images anywhere.

```
┌──────────────────────────────────────────────────────────────┐
│  [wordmark]              [ search ]                    [github]│  top bar, hairline under
├────────────┬─────────────────────────────────┬───────────────┤
│ 2026       │  PRE-MARKET · 09:05 IST         │ On this page  │
│  Jul       │  Nifty & Sensex — 11 Jul 2026   │  Pre-Market   │
│   11 ◄     │  ───────────────────────────    │   Markets     │
│   10       │  Markets Data                   │   News        │
│   09       │  [ metric table, mono, aligned ]│   Signal      │
│  Jun       │  Important News                 │  EOD          │
│ 2025       │  [ headline → source link ]     │   Close       │
│            │  Signal:  Mildly Long  +4       │   News        │
│            │  ⚠ not financial advice         │               │
│            │  ═══════════════════════════    │               │
│            │  EOD · 16:10 IST                │               │
│            │  How markets performed today    │               │
│            │  [ closes, breadth, top-10 news]│               │
│            │  Conclusion                     │               │
└────────────┴─────────────────────────────────┴───────────────┘
```

- **Left:** date tree, reverse-chron, counts per month. Active day marked with the accent + a left rule, not a fill.
- **Center:** the day. Max content width ~720px for readability even on wide screens.
- **Right:** on-this-page ToC, two primary anchors (Pre-Market, EOD).
- **Mobile:** columns collapse; date tree → drawer, ToC → top disclosure. Content column full-width.

---

## Signature element — the signal readout

The one memorable thing. Keep everything around it quiet; let this be the focal moment.

**Metric → vote table** (Geist Mono, tabular, hairline rows):

```
INPUT              VALUE        VOTE
GIFT Nifty         +0.42%        +1
S&P 500 o/n        −0.15%         0
Nasdaq o/n         −0.30%        −1
FII net (prev)     −2,140 cr     −1
DII net (prev)     +1,880 cr     +1
USD/INR            83.62 ▲       −1
India VIX          14.8  ▲       (conviction ↓)
...
────────────────────────────────
NET BIAS           Mildly Long   +4
```

- Votes colored with `--up` / `--down` / `--flat`. Everything else greyscale.
- The net line: serif label ("Mildly Long") + mono score (`+4`). VIX/Brent shown but visibly set apart (they modify conviction / add context, they don't vote on direction).
- **Warning banner** directly beneath, always present, muted styling (not alarmist red — it's a standing caveat, not an error):
  > *Not financial advice. An automated guess from public data. Often wrong, especially about the close.*

**Restraint check:** no gauges-with-gradients, no animated needles, no glow. The signal earns attention through precise alignment and the one bit of color that means something — consistent with the "quiet reference" thesis.

---

## Page states

Four states beyond the "full trading day" need explicit styling — all of them stay inside the quiet-reference voice. None are errors; none get alarm styling.

**Awaiting EOD** (morning → ~16:15 IST). Below the Pre-Market section, where EOD will land: a hairline, then a muted mono eyebrow-style line — `EOD · EXPECTED ~16:15 IST` — in `--text-muted`. Nothing else. No spinner, no skeleton, no empty boxes. When the EOD write lands, content replaces this line with **zero layout shift** above it (the quality-floor rule).

**Degraded data** (some inputs unavailable). In the signal table, a missing metric renders its value as `—` with `unavailable` in muted mono; its vote is `0` in `--flat`. One quiet line beneath the table, muted, body size: "2 of 11 inputs unavailable this morning." Never red — missing data is a fact, not a failure.

**Signal suppressed** (≥4 inputs missing — ORCHESTRATION.md §5b). The table renders whatever was fetched; the NET BIAS line is replaced by a muted serif line: "Insufficient data for a signal this morning." The warning banner still renders (it's a standing fixture, not conditional).

**Weekend / holiday.** Single-section page: eyebrow (`WEEKEND` or `MARKET HOLIDAY · REPUBLIC DAY`), serif title, news list. No metrics table, no signal, no ToC split — the right rail may collapse to a single "News" anchor.

---

## Motion

Minimal by intent — extra animation would read as generated and undercut the calm. Permitted: subtle hover underline on links, a quiet fade on the mobile drawer. `prefers-reduced-motion` respected. No scroll-jacking, no reveal choreography.

---

## Quality floor

- Responsive to mobile (column collapse described above).
- Visible keyboard focus (accent outline).
- Reduced motion honored.
- Contrast: text/`--bg` and muted/`--bg` meet WCAG AA.
- No layout shift when EOD content appends below Pre-Market.

---

## What to avoid

- Cards, drop shadows, rounded container corners (use rules + space).
- Red/green anywhere except % changes and votes.
- The lavender accent used for emphasis in body text.
- Inter (deliberately not used — the point is to not look like every AI site).
- Geist Pixel / dotted display faces (rejected — too "toy/dev-tool" for a finance audience).
- Images, hero art, illustrations — the site is text + rules, and that's the identity.
- Hardcoding the brand name into any style, template, or component.
