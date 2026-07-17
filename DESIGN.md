# DESIGN.md — Daily Indian Markets Reference

> A reusable design reference for the coding agent. Colors, type, spacing, structure, and the reasoning behind them, so every page follows one visual language.
> **Brand name is a variable** (currently "niftyfiftyone") — never hardcode it into styles or components. See PLANNING.md §11.

---

## Design thesis

A **dashboard reference**, not a trading terminal and not a dev tool. The page should feel calm, dense, and instrumented — a well-set data surface you consult, like a screenshot of a moment rather than a live feed. Warmth comes from the serif headings; rigor comes from bordered cards and monospace numbers. The market's red/green is the *only* saturated color on the page, carried into card tints where it directly reports direction — never decoration.

Two references were deliberately combined:
- **Structure** from a docs shell (three columns: date tree · content · on-this-page) plus bordered, radiused cards for every content block.
- **Skin** from a dark, data-dense dashboard aesthetic (dexscreener-style density, a faint background grid, tabular numbers) — but static: no live updates, no animated numbers, no client-side data fetching. Everything here is build-time. **This is still governed by CLAUDE.md Hard Rule 7 (zero client JS)** — "dexscreener-inspired" means adopting its visual density and grid-canvas language in pure CSS, not its live-terminal behavior.

**Card override:** as of 2026-07-15 this thesis explicitly overrides CLAUDE.md Hard Rule 8 ("no cards, shadows, or rounded containers") for card containers and their single radius value. Hairlines still govern everything *inside* a card — table rows, list items, internal dividers stay unradiused 1px rules. Shadows remain out of scope entirely; depth comes from the layered surface ramp and the border, never a drop shadow.

---

## Color

Dark canvas with a **layered near-black ramp** — never pure `#000`, never one flat black. Cool slate undertone. Greyscale structure; saturated color only where it means something.

| Token | Hex | Use |
|---|---|---|
| `--bg` | `#09090B` | Deepest page canvas (sidebar, outer shell) |
| `--bg-panel` | `#0E0E12` | Main content column — one step up from canvas |
| `--surface` | `#141418` | Card bodies, list rows |
| `--surface-2` | `#1A1A20` | Card heads, table headers, notice strips |
| `--surface-3` | `#22222A` | Hover, NET BIAS row, subtle emphasis fills |
| `--rule` | `#2C2C36` | Internal hairlines (table/list rows inside a card) |
| `--rule-strong` | `#3A3A46` | Card borders |
| `--grid-line` | `rgba(237, 237, 234, 0.035)` | Background grid texture on `--bg` only — barely-there, never competes with content |
| `--text` | `#EDEDEA` | Primary text (off-white, warm, not #FFF) |
| `--text-muted` | `#9A9AA2` | Secondary text, labels, timestamps |
| `--accent` | `#8B8BF5` | Links, active nav, focus — one calm lavender, low saturation |
| `--up` | `#4ADE80` | Positive % change, Long vote (+1) — **meaning only** |
| `--down` | `#F87171` | Negative % change, Short vote (−1) — **meaning only** |
| `--flat` | `#9A9AA2` | Zero vote / unchanged (same as muted) |
| `--up-fill` | `rgba(74, 222, 128, 0.12)` | Stat-card background tint when its number is positive — **meaning only**, never decorative |
| `--down-fill` | `rgba(248, 113, 113, 0.12)` | Stat-card background tint when its number is negative — **meaning only** |
| `--up-border` | `rgba(74, 222, 128, 0.35)` | Stat-card border tint, positive — a full-strength `--up` border reads alarmist |
| `--down-border` | `rgba(248, 113, 113, 0.35)` | Stat-card border tint, negative |
| `--radius` | `10px` | Card radius — cards and stat cards. |
| `--radius-sm` | `6px` | Compact-control radius — sidebar day chips, the search field. Exactly these two radius values exist; nothing else gets rounded. |

**Depth rule:** chrome (header / sidebar) · content panel · card body · card head are four distinct steps on the ramp. Readers should feel planes, not a void.

**Rules for color**
- Red/green appear **only** on numeric % changes, signal votes, and the tinted backgrounds of stat cards reporting those same numbers. Never on borders, headings, or decoration.
- The lavender accent is for interaction (links/active/focus) only — not for emphasis in prose.
- Background variation stays on the greyscale ramp (no tinted brand washes). If a color isn't carrying meaning, it shouldn't be saturated.

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
| `stat-hero` | 26 / 1.15 | Geist Mono 600, tabular-nums | Homepage hero-strip stat numbers only — deliberately medium, a step up from `data` but not a giant display digit |

**Smart quotes on**, sentence case for UI, tabular figures wherever numbers stack.

---

## Structure — the card system

Structure is carried by **bordered cards** (`--surface` fill, 1px `--rule-strong` border, `--radius` corner) plus **hairlines inside them**. Two radius values (`--radius` for cards, `--radius-sm` for compact controls), no shadows.

- **Section dividers:** a full-width hairline above each major section (Pre-Market, EOD).
- **Cards:** major content blocks (Signal readout, Close table, News list, homepage stat cards) sit in a **bordered card** — a 1px `--rule-strong` box, `--radius` corners, a mono label-strip head, and a body. Adjacent cards share the same border/radius language so the page reads as an instrumented dashboard, not a loose stack of tables.
- **Table rows / list items inside a card:** each metric/news row separated by a bottom hairline, unradiused. No zebra striping, no cell borders.
- **Column split:** the three-column shell separated by vertical hairlines where two columns meet (as in the reference).
- **Background grid:** the outer canvas (`--bg`) carries a faint two-axis grid texture in `--grid-line` — pure CSS `repeating-linear-gradient`, decorative only, never inside a card body (cards are opaque `--surface`, so the grid only shows through the gutters).
- **Eyebrows:** each section opens with a Geist Mono uppercase label (e.g. `PRE-MARKET · 09:05 IST`) above the serif heading. The eyebrow encodes *real information* (phase + timestamp), not decoration.

**Spacing:** base unit 8px. Section vertical rhythm 40–56px (tighter than pure editorial so cards feel organised). Row padding 12–14px vertical. Density comes from alignment and shared borders, not cramming.

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

- **Left:** the date tree rendered as a **compact calendar**: year as a serif group head, month as a mono uppercase eyebrow with count, days as a grid of small bordered mono chips (`--radius-sm`, `--surface` fill, hairline border). Each chip carries a `title` tooltip with the full weekday + date. Hover: accent border. Active day: accent border + accent text — chips carry their own border, so the left-rule treatment does not apply here.
- **Center:** the day. Max content width ~720px for readability even on wide screens.
- **Right:** on-this-page ToC, two primary anchors (Pre-Market, EOD).
- **Mobile:** columns collapse; date tree → drawer, ToC → top disclosure. Content column full-width.

### Chrome & nav

The header is a **two-row bar** (`--sl-nav-height: 6rem`, custom `Header.astro` override):

Both rows sit on the deepest `--bg` black — **hairlines, not grey fills, do the separating** (a hairline between the rows, a `--rule-strong` hairline under the whole bar). The main row is height-locked (`--sl-nav-height` minus the 2.2rem ticker), so its contents are exactly vertically centered.

**Row 1 — main bar:**
- **Wordmark:** the site name set in Source Serif 4 600 (~21px), `--text` color like a masthead — never the accent at rest. Accent appears on hover only (it's a link, so interaction). No logo image, no icon mark — the serif itself is the identity.
- **Search:** a `--surface` field with a 1px `--rule-strong` border and `--radius-sm` corners; border shifts to accent on hover. Centered, max ~30rem.
- **Right group** (hidden on mobile): an `ABOUT` text link (mono label, accent on hover) · a **bookmark CTA chip** — mono label + `⌘D` kbd cap in a `--radius-sm` bordered chip, tooltip explains Cmd+D/Ctrl+D; it's a static hint, not a JS button — · the Starlight theme select.

**Row 2 — market ticker strip**, the financial-site signature: full-bleed row on `--bg` under a hairline, horizontally scrollable on narrow screens (no visible scrollbar). Opens with a mono **date stamp** (`AS OF 14 JUL CLOSE · IST`), then Nifty 50 / Sensex / Bank Nifty: mono label in muted, close value in `--text` tabular mono, delta % colored `--up`/`--down` (meaning). Built at compile time from the latest EOD sidecar; if no EOD data exists anywhere, the strip falls back to `ARCHIVE · N SESSIONS INDEXED`.

**Honesty rule:** the ticker is a dated snapshot, never presented as live — always stamped "As of", no motion, no blinking, no auto-refresh. (CLAUDE.md rule 7 — zero client JS.)

### Homepage layout

The homepage differs from a day page: it opens with a **masthead hero** (the site h1 in serif, the tagline directly beneath in serif italic `--text-muted`, then a hairline), then the **hero stat strip**, then the full latest day, then a **Recent Days card grid**. The tagline comes from `src/config/site.ts` — never hardcoded.

**Hero stat strip** — flex row of small cards, each `flex: 1 1 0` (equal-width regardless of label/value length — 1, 3, or 4 stats all come out the same size), floored at 160px and capped at 260px so a lone card never becomes a full-width slab. Each card: a mono label and a medium `stat-hero`-scale number, background tinted `--up-fill`/`--down-fill` and border tinted `--up-border`/`--down-border` by sign:

- **Before today's EOD lands:** a single card — today's Pre-Market Net Bias (score + label, e.g. `+4` / "Mildly Long"), tinted by the score's sign, flat/untinted if the score is `0`.
- **After today's EOD lands:** three cards — Nifty, Sensex, Bank Nifty close % change, each tinted by its own sign.
- **Omitted entirely** when: the day is a weekend/holiday page (no metrics at all), or the signal is suppressed (≥4 inputs missing — never show a placeholder or an invented number, same rule as the signal table itself).

```
┌───────────────┬───────────────┬───────────────┐
│ NIFTY 50      │ SENSEX        │ BANK NIFTY    │
│ +0.84%        │ +0.71%        │ +1.12%        │   ← stat-hero, tinted --up-fill
└───────────────┴───────────────┴───────────────┘
[ full latest-day content, exactly as a day page ]
─────────────────────────────────────────────────
RECENT DAYS
┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│ 16 Jul 2026    │ │ 14 Jul 2026    │ │ 13 Jul 2026    │
│ Nifty +0.42%   │ │ Nifty −0.18%   │ │ Pre-market: … │   ← card grid, auto-fill
│ · Mildly Long  │ │ · Neutral      │ │                │
└───────────────┘ └───────────────┘ └───────────────┘
```

- **Recent Days** grid: `grid-template-columns: repeat(auto-fill, minmax(220px, 1fr))`, collapsing to 1 column on mobile. Each card: date + title (serif, small) + the existing one-line summary (`daySummary()` in `src/lib/dayList.ts`) as a small tinted delta chip when it's a % figure, plain muted text otherwise (e.g. "Weekend — news only").
- Below-the-fold content (the full latest day) is unaffected by the hero strip — it is not a summary or a truncation, per the existing "always shows fresh, fully-rendered content" rule.

---

## Signature element — the signal readout

The one memorable thing. Keep everything around it quiet; let this be the focal moment.

**Metric → vote table** (Geist Mono, tabular, hairline rows, inside the Signal card):

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

**Restraint check:** no gauges-with-gradients, no animated needles, no glow. The signal earns attention through precise alignment and the one bit of color that means something.

---

## Page states

Four states beyond the "full trading day" need explicit styling — all of them stay inside the card system.

**Awaiting EOD** (morning → ~16:15 IST). Below the Pre-Market section, where EOD will land: a hairline, then a card with a muted mono eyebrow-style line — `EOD · EXPECTED ~16:15 IST` — in `--text-muted`. Nothing else. No spinner, no skeleton, no empty boxes. When the EOD write lands, content replaces this card with **zero layout shift** above it (the quality-floor rule).

**Degraded data** (some inputs unavailable). In the signal table, a missing metric renders its value as `—` with `unavailable` in muted mono; its vote is `0` in `--flat`. One quiet line beneath the table, muted, body size: "2 of 11 inputs unavailable this morning." Never red — missing data is a fact, not a failure.

**Signal suppressed** (≥4 inputs missing — ORCHESTRATION.md §5b). The table renders whatever was fetched; the NET BIAS line is replaced by a muted serif line: "Insufficient data for a signal this morning." The warning banner still renders (it's a standing fixture, not conditional). The homepage hero strip is omitted for this day, same rule.

**Weekend / holiday.** Single-section page: eyebrow (`WEEKEND` or `MARKET HOLIDAY · REPUBLIC DAY`), serif title, news list. No metrics table, no signal, no ToC split — the right rail may collapse to a single "News" anchor. No hero strip on the homepage for this day.

---

## Motion

Minimal and functional, never decorative — extra animation would undercut the calm and read as generated.

- **Card hover:** 150ms ease-out transition on `border-color` and `background`, with a 1px `translateY(-1px)` lift. No scale, no glow, no shadow.
- **Chip / control hover** (sidebar day chips, search, wordmark): 150ms ease-out on `border-color` / `color` only — no lift on compact controls.
- **In-page navigation:** `scroll-behavior: smooth` on the root for ToC/sidebar anchor jumps, plus a quiet fade on the mobile drawer.
- **Numbers never animate** — no counting-up, no blinking ticks, no live-terminal effects. Every number on the page is a static build-time value.
- `prefers-reduced-motion` respected (zeroes all transition/animation durations). No scroll-jacking, no reveal choreography.

---

## Quality floor

- Responsive to mobile (column collapse described above; hero strip and Recent Days grid both collapse to 1 column).
- Visible keyboard focus (accent outline).
- Reduced motion honored.
- Contrast: text/`--bg` and muted/`--bg` meet WCAG AA — including text set on `--up-fill`/`--down-fill` tinted card backgrounds (`--up`/`--down` text colors were chosen light enough to hold AA on both `--surface` and the tints).
- No layout shift when EOD content appends below Pre-Market, or when the hero strip swaps from Pre-Market bias to EOD closes.

---

## What to avoid

- Heavy drop shadows or glow — depth comes from the surface ramp and the border, never a shadow.
- Gradient fills — flat `--surface`/tint colors only.
- Radius values beyond the two sanctioned ones (`--radius` for cards, `--radius-sm` for compact controls — nothing in between, nothing larger).
- The accent color at rest on brand chrome (wordmark, header) — accent is for interaction states only.
- Red/green anywhere except % changes, votes, and their direct stat-card tints.
- The lavender accent used for emphasis in body text.
- Animated or blinking numbers, live-ticker JS behavior, client-side data fetching — the page is a static build-time artifact (CLAUDE.md Hard Rule 7), regardless of visual inspiration.
- Sans-only or mono-only headings — the serif display face is deliberately kept for warmth against the data-dense body.
- Images, hero art, illustrations, stock photography — the site is text + cards + rules, and that's the identity.
- Hardcoding the brand name into any style, template, or component.
- Empty meta lines (e.g. "Leaders: · Laggards:") — omit a field when the data is missing; never print a hollow label.
