d# Design guideline — AFA 2026

This is the contract for visual work on the rest of the site. Everything
below is what's already shipped on the homepage. When you build a new
page or update an existing one, match these rules unless there's a
specific reason not to — and call that exception out.

> Source of truth: `src/app/page.tsx` (homepage) + `src/app/globals.css`
> + `src/components/*`. If anything in this doc disagrees with the
> codebase, the codebase wins and this doc gets corrected.

---

## 1. Theme system

- Light is the default theme. Dark is opt-in via the toggle in the
  header. Most pages should look correct in both — never hard-code a
  color that breaks one of them.
- Theme attribute lives on `<html>`: `[data-theme="dark"]`. The
  `dark:` Tailwind variant is wired to that (see globals.css custom
  variant) — `dark:text-fg`, `dark:bg-canvas`, etc. all work.
- Local theme overrides: drop `.theme-light` or `.theme-dark` on a
  section to invert just that subtree (the awards section uses
  `theme-light` on a colored slab). The `.theme-dark` override on
  `<SiteFooter>` is the canonical example.

### Token shortlist (use these, not raw hex)

| Token | Light | Dark | Use for |
|---|---|---|---|
| `--color-canvas` (`bg-canvas`) | `#fdfcf0` cream | `#080f11` NR Black | Page background |
| `--color-surface` (`bg-surface`) | `#f1f0e4` system white | `#0e1518` | Card surfaces, secondary buttons |
| `--color-elevated` (`bg-elevated`) | `#fffefa` | `#141c20` | Hover state, soft elevation |
| `--color-border-subtle` | `#e5e4d8` | `#1f272b` | Hairline rules, default borders |
| `--color-border-default` | `#cdc9b8` | `#2a343a` | Stronger borders, focus rings |
| `--color-fg` (`text-fg`) | `#080f11` | `#fdfcf0` | Body text default |
| `--color-fg-body` | `#1a242a` | `#f1f0e4` | Long-form copy |
| `--color-fg-muted` (`text-fg-muted`) | `#6a7173` | `#888c8d` | Eyebrows, secondary metadata |

### Brand-fixed colors (never theme-aware)

These are the same on light and dark — use them as accents, never as
the primary surface color.

- `--color-nr-green` `#1ce783` — primary brand accent
- `--color-nr-green-tint` `#aaf2ce` — gradient stop, lighter green
- `--color-nr-blue-1` `#a3e5e5` — pale cyan, used in Awards section bg
- `--color-nr-blue-2` `#3d9dff` — accent blue
- `--color-nr-magenta-2` `#dc466f` — accent magenta
- `--color-nr-ember-1` `#f7d354` — gradient stop, yellow
- `--color-nr-ember-2` `#ff7f4d` — accent orange (Regions accent)
- `--color-nr-black` `#080f11` — NR Black (use over `text-fg` only when
  you intentionally want light-theme behavior in a dark-theme container)
- `--color-nr-white` `#fdfcf0` — Bright White (cream)
- `--color-nr-white-system` `#f1f0e4` — System White, used for header
  text on the always-black pill

### Other theme-aware tokens

- `--hero-panel-rgb` — RGB tuple for the hero halo. Cream on light,
  NR Black on dark. Use via `rgb(var(…))` / `rgba(var(…), …)`.

---

## 2. Typography

Three families, all set up via `next/font/google` and exposed as CSS
vars:

- **Mona Sans** (`var(--font-display)`): condensed black display face.
  Only via the `.display` utility. Brutalist hero headlines, brand
  marks. Always uppercase by default (override with `!normal-case` if
  needed — the hero h1 does this).
- **Inter** (`var(--font-sans)`): everything else. Body copy, headings,
  buttons, nav, cards.
- **Geist Mono** (`var(--font-mono)`): eyebrows, dates, code blocks,
  countdown digits, status labels.

### Type scale

| Utility | Size | Weight | Tracking | Use for |
|---|---|---|---|---|
| `.display` | inherits | 900 | -0.02em | Hero h1 (with size override), brand mark in header |
| `.text-sub-large` | clamp(2.25rem, 5vw, 4rem) | 600 | -0.066em | Section h2s ("Same Friday.", "Why are we doing this", page titles on subpages) |
| `.text-sub-small` | 20px | 600 | -0.03em | Sub-hero paragraph (under the headline) |
| `.eyebrow` | 11px mono uppercase | 400 | 0.16em | Section labels (`THREE REGIONAL COHORTS`, `PRIZES (TENTATIVE)`) |
| `text-[14px] font-medium` (Inter) | 14px | 500 | — | Card body copy (Pillars, Awards) |
| `text-[16px] font-medium` (Inter) | 16px | 500 | — | Schedule rows, secondary content |
| `text-[18px] font-medium tracking-[-0.02em]` | 18px | 500 | -0.02em | Marquee items, prominent links |
| `text-[20px] font-bold tracking-[-0.02em]` | 20px | 700 | -0.02em | Card titles (Pillars), small h3s |
| `text-[32px] font-bold tracking-[-0.02em]` | 32px | 700 | -0.02em | Card amounts (Awards), card emphasis (Regions labels) |

Heading defaults: `<h1>–<h4>` are scoped to Inter SemiBold tight tracking
in `globals.css` base layer. **Never rely on the default for visible
headings — opt into a class explicitly** so the intent is clear.

### Eyebrow + rule pattern

The card eyebrow pattern across Pillars / Awards is consistent:

```jsx
<div className="flex flex-col gap-2">
  <p className="font-mono text-[12px] font-medium leading-none">
    01 / VELOCITY
  </p>
  <div aria-hidden className="h-px w-full bg-nr-black" />
</div>
```

Mono medium 12px, then a 1px black horizontal rule. Use this on any
card where you want a labeled section header.

---

## 3. Buttons

Live in `src/components/ui/button.tsx`. Variants: `primary` (default),
`secondary`, `ghost`, `danger`. Sizes: `sm`, `md`, `lg`, `xl`.

| Size | Height | Padding | Text | When |
|---|---|---|---|---|
| `sm` | 32px | px-3 | text-xs | Compact UI, table rows |
| `md` | 40px | px-5 | text-sm | Default forms |
| `lg` | 48px | px-7 | text-base | Section CTAs |
| `xl` | 64px | px-9 | text-base | Hero CTAs (use these on landing pages) |

Variant styles:

- **Primary**: `bg-fg text-canvas` — inverted foreground. Black-on-cream
  in light, cream-on-black in dark. The high-contrast workhorse.
- **Secondary**: `bg-surface text-fg` — soft surface tone. Pairs with
  primary, doesn't compete.
- **Ghost**: `text-fg hover:bg-surface` — text-only with hover.
- **Danger**: `bg-danger text-fg` — destructive actions only.

Always use the `Button` component, not raw `<button>` styling, so the
variants stay consistent.

### Pill links (header-style)

Used in the dark header pill for nav, Sign in, My team. Pattern:

```jsx
className="inline-flex h-[70px] items-center rounded-pill px-4 text-lg font-medium text-nr-white-system/80 transition-colors hover:bg-nr-white-system/10 hover:text-nr-white-system"
```

`bg-[#151b20]` baseline + `hover:bg-[#1f262c]` is the variant used when
the link should look like a button (Sign in, signed-in user pill).

---

## 4. Layout & spacing

### Page structure

```jsx
<section className="…optional bg/theme override…">
  <Reveal className="mx-auto max-w-7xl px-4 py-20 md:px-6 md:py-28">
    {/* 1. EyebrowLabel (optional) */}
    {/* 2. h2 in .text-sub-large */}
    {/* 3. supporting p */}
    {/* 4. content grid */}
  </Reveal>
</section>
```

- Containers cap at `max-w-7xl` (1280px) and use `mx-auto`.
- Horizontal padding: `px-4 md:px-6` (16px / 24px).
- Vertical padding: `py-20 md:py-28` (80 / 112) for most sections.
  Tight sections (Regions): `py-16 md:py-24`. Heavy/feature sections
  (Timeline): `py-32 md:py-40`.
- Wrap content in `<Reveal>` for the scroll-fade-in effect, unless
  there's a reason not to (e.g. the hero, which is always above the
  fold).

### Section header block

```jsx
<div className="mb-10 flex flex-col gap-3">
  <EyebrowLabel>SECTION LABEL</EyebrowLabel>
  <h2 className="text-sub-large">
    Title.
    <br />
    <span className="text-nr-…">Accent line.</span>
  </h2>
  <p className="max-w-2xl text-base text-fg-body">
    One-paragraph supporting copy.
  </p>
</div>
```

- Eyebrow → h2 → p, in that order.
- The accent on h2's second line uses a brand color. **Each section
  picks one accent and sticks with it**:
  - Hero → `text-nr-green` (sometimes recolored via WordRotator)
  - Regions → `text-nr-ember-2`
  - Awards → `text-nr-blue-2`
  - CTA banner → `text-with-bg` highlighter on NR Green
- Supporting paragraph maxes at `max-w-2xl`. Long-form prose maxes at
  `max-w-3xl`.

### Section dividers

The full-bleed banded `<SectionDivider>` (`color="green" | "blue"`,
optional `flip`) is the divider of choice between major homepage
sections. For everything else (subpages, internal section breaks),
use a thin rule:

```jsx
<hr className="border-t border-border-subtle" />
```

Don't use both at once. Don't reach for `border-b` on the section
itself — it's been removed everywhere.

---

## 5. Card patterns

There are three established card patterns. Pick the one that matches
the visual weight you need.

### A. Plain Card (`<Card>` from `ui/card.tsx`)

Default surface card. Soft border, surface background, theme-aware.
Use for utility content (settings, list items, profile cards, etc.).

```jsx
<Card className="dot-grid-corner">
  <EyebrowLabel className="mb-2">_01 / SECTION</EyebrowLabel>
  <CardTitle>Title</CardTitle>
  <CardDescription className="mt-3">
    Body copy.
  </CardDescription>
</Card>
```

Add `dot-grid-corner` for the upper-right dot pattern (playbook motif).

### B. Gradient-slab cards (Pillars / Awards / Regions)

A single rounded gradient slab wraps a row or grid of cream cards;
4px frame and 4px inter-card seams let the gradient peek through.
**Each gradient palette = one section's identity:**

- **Lime → NR Green** `from-[#d2f936] to-[#1ce684]` — Pillars
- **Cyan → Blue** `from-[#a3e5e5] to-[#3c9dff]` — Awards
- **Yellow → Orange** `from-[#f7d354] to-[#ff7f4d]` — Regions

Standard structure:

```jsx
<div className="grid grid-cols-1 gap-1 rounded-[22px] bg-gradient-to-r from-[#…] to-[#…] p-1 md:grid-cols-2 md:grid-cols-3 …">
  <article className="flex flex-col gap-6 rounded-[20px] border border-nr-black bg-nr-white p-8 text-nr-black">
    {/* eyebrow + rule */}
    {/* content */}
  </article>
</div>
```

Defaults that are always the same:

- Outer: `rounded-[22px] p-1 gap-1`. (Pillars uses `rounded-[16px]` —
  the older variant; new sections should use 22px.)
- Inner card: `rounded-[20px] border border-nr-black bg-nr-white p-8
  text-nr-black`.
- Card content gap: `gap-6` between sections inside the card, `gap-4`
  inside a content block, `gap-2` for the eyebrow-+-rule unit.

Stack vertically on mobile (`grid-cols-1` or `flex-col`), expand to
horizontal at `md:` breakpoint.

### C. Mixed slab (Regions: 3-up + wide)

A composite gradient-slab layout with a row-of-equal-cards on top and a
single full-width card on the bottom. See `<section
className="regions-section-bg">` in `page.tsx` for the canonical
example. Use this when you have a related set of items + one shared
piece of metadata that applies to all of them.

### Card content rules

- Text inside a colored-slab card is always **NR Black on NR White**
  (theme-fixed) — those cards are pre-decided to read as light slabs in
  any theme.
- Text inside a plain `<Card>` uses theme tokens (`text-fg`,
  `text-fg-body`, `text-fg-muted`).
- Don't add a soft border AND a background tint AND a gradient frame —
  one of those is enough. Slab cards skip the soft border on the slab
  itself; plain cards skip the gradient frame.

---

## 6. Status pills & eyebrows

### `<EyebrowLabel>`

Small mono-uppercase label. Used above headlines and in card headers.
Always wrap with the component — don't recreate the styling inline.

### `<StatusPill>`

Tone-tinted pill with optional pulsing radar dot. Tones: `green`,
`blue`, `magenta`, `ember`, `muted`. Theme-aware via the `dark:`
variant — dark text on a faint tint in light mode, bright accent text
on a faint tint in dark mode (the `magenta` tone is dark in both).

```jsx
<StatusPill tone="green" pulse>Registration open</StatusPill>
```

Use sparingly — these are for **status**, not generic labels. If it's
just a tag, use a regular eyebrow or a `Card`-corner label.

---

## 7. Header & navigation

The header is a sticky outer band (cream/dark with backdrop blur)
containing a floating black pill that holds everything. Always-black
regardless of page theme — the pill is the inverted island.

Rules for anything that lives in the header pill:

- 70px tall hit area, `rounded-pill`.
- `text-nr-white-system/80` text by default, `hover:text-nr-white-system`
  + `hover:bg-nr-white-system/10` (or `/15` for buttoned items).
- Sign in / signed-in user pill = the primary CTA pattern: solid
  `bg-[#151b20]` baseline, `hover:bg-[#1f262c]`.
- Theme toggle = a 70×70 pill button, transparent by default.
- The brand mark (`<NRLogo>` + `AFA 2026`) is the only thing that may
  use `.display`/uppercase inside the header.

---

## 8. Footer

Forced `theme-dark` so it always inverts from the page bg.
Two-column symmetric layout (`flex flex-col … md:flex-row`):

- Left: brand attribution row (label · separator · author email).
- Right: nav links row (Schedule · About · Code of conduct).

Mid-dot separators (`<span aria-hidden>·</span>`) only show at `md+`.

Don't add disconnected meta lines, version eyebrows, or "internal NR
event" sublines — keep it lean.

---

## 9. Marquee (PhaseBanner)

The scrolling phase + key-fact strip. Inter Medium 18px, 36px vertical
padding, with custom 16×16 currentColor SVG icons. **Only used on the
homepage**. Don't add it to subpages — it's a landing-page-scale
element and would compete with the page title.

Each item's icon comes from `marquee-icons.tsx`. Match the icon to the
content type:

- `ThunderIcon` — phase / live state
- `DateIcon` — calendar / date
- `TimeIcon` — clock / regions
- `BookmarkBoldIcon` — featured / saved
- `BoldStarIcon` — voted / favorite
- `BarChartIcon` — counter / metrics
- `CommentIcon` — chat / discussion

---

## 10. Hero patterns

The homepage hero is the maximum visual treatment. Subpages should not
replicate the full hero — they get the **lighter page-header** pattern
instead:

```jsx
<header className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-16 md:px-6 md:py-24">
  <EyebrowLabel>SECTION LABEL</EyebrowLabel>
  <h1 className="text-sub-large">
    Page title.
  </h1>
  <p className="max-w-2xl text-lg text-fg-body">
    One-paragraph what-this-page-is-about.
  </p>
</header>
```

- No animated background.
- No `min-h-[100svh]`.
- `text-sub-large` h1 (mixed case), not `.display`.
- 72/96px vertical padding.
- Optional follow-up rule (`<hr className="border-t
  border-border-subtle" />`) before the first content section.

When in doubt, look at how the homepage header below the hero treats a
section heading and copy that — same eyebrow → h2 → p sequence.

---

## 11. Background images & textures

- `regions-section-bg` (theme-aware bg image) is **only** on the
  Regions section. Don't reuse the file; if you need decorative bg art
  for another section, design it into the gradient-slab system or pick
  a brand-fixed accent.
- `dot-grid-corner` (subtle dot pattern in the upper-right) is the
  default decorative accent for plain `<Card>` surfaces. Cheap and
  effective — don't reach for additional patterns.
- Avoid stock textures, photos, or any imagery that can't be themed
  via `currentColor`/CSS variables.

---

## 12. Content rules

- **Sentence case** for page titles and section headlines (per the
  Brand Playbook). The only place forced UPPERCASE is allowed:
  `.display` on the hero, `EyebrowLabel`, `StatusPill`, mono-monocaps
  metadata. Long titles in uppercase = no.
- Brand abbreviations stay capitalized (`AFA`, `NR`, `EPD`, `CTO`,
  `CSV`, `AI`).
- Em dash with thin spaces around it for parenthetical flair (`Day 1 —
  the conference`). Don't use double hyphens.
- Use NR-flavored verbs: "ship", "queue", "lock", "wrap", "kickoff".
- Numerals everywhere: `8 AM`, `4:30 PM`, `30 min`, `$1,000`. Spell
  out only when the sentence rhythm needs it.

---

## 13. Common mistakes to avoid

- **Don't** put `border-b` on a section. Use `<SectionDivider>` or
  a thin `<hr>` instead.
- **Don't** force a color in a way that fails one theme. If you can't
  test the other theme, use semantic tokens (`text-fg`,
  `bg-canvas`) — they handle the swap for you.
- **Don't** mix the brutalist `.display` style with the rest of the
  body in the same heading block. Pick one register per section.
- **Don't** introduce new size or color tokens. If you need something
  new, add it to `globals.css` and document it here so it stays
  reusable.
- **Don't** stack the gradient-slab card pattern on top of itself —
  one slab per section. Don't nest gradient slabs.
- **Don't** ship a heading without a class. The `<h1>–<h4>` defaults
  exist as a fallback; visible headings should always opt into one of
  the three explicit classes (`.display`, `.text-sub-large`,
  `.text-sub-small`) or a Tailwind size + weight + tracking trio.
- **Don't** import lucide icons just for one-off use. The marquee uses
  custom SVGs in `currentColor`, follow that pattern (or add to it) so
  icons stay theme-aware and styleable.

---

## 14. Component checklist (when building a new page)

When you sit down to update or build a page, make sure all of these are
true before considering it done:

- [ ] Page header uses the section header block pattern (eyebrow → h2 → p).
- [ ] Section padding follows the 80/112 (or 128/160) rhythm.
- [ ] No `border-b` on sections; thin `<hr>` between content blocks if
      needed.
- [ ] Cards use one of the three established patterns (A / B / C).
- [ ] Buttons use `<Button>` with the right variant + size.
- [ ] All text uses tokens (`text-fg`, `text-fg-body`, `text-fg-muted`)
      or one of the three typography utilities. No hex in text colors.
- [ ] Both light and dark themes look correct. Toggle and check.
- [ ] Status indicators use `<StatusPill>`; metadata labels use
      `<EyebrowLabel>`.
- [ ] `<Reveal>` wrapped around content sections that aren't above the
      fold.
- [ ] Page title in the metadata (`<title>`) updated to "Page name —
      AFA 2026".
- [ ] Mobile layout works — content stacks, container padding holds at
      `px-4`, no horizontal scroll.
