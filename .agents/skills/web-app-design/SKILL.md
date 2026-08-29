---
name: web-app-design
description: "Follow the existing design system when editing, creating, or reviewing UI. Use whenever working on views, components, styles, or any file that produces HTML/CSS — even if the user does not explicitly mention the design system."
---

# Web App Design

Match the design system already in this repo. Do not invent a parallel look.

**Announce at start:** "I'm using the web-app-design skill."

## Before writing any UI

Inspect what this project already uses, then copy it:

1. Tokens — colors, type, spacing, radii (CSS variables, Tailwind config, theme files)
2. Shared primitives — button/input/card helpers or component library
3. Existing screens adjacent to the work
4. Any design-system doc in the repo (README, AGENTS.md, `docs/`)

If helpers or components already exist for buttons, inputs, or layout, use those. Add a new primitive only when nothing covers the case — and add it next to the existing ones, not inline in a one-off view.

## Decision rules

1. **Clarity > cleverness** — If it isn't instantly understandable, redesign it.
2. **Restraint** — Add visual weight, color, or ornament only when it solves a real user problem.
3. **Hierarchy via type and space** — Font weight, size, and spacing first. Color second, and sparingly.
4. **Works small** — Patterns must work at a 375px-wide viewport and pass WCAG AA.
5. **Subtle interaction** — Hover: slight border or color shift. No dramatic scales, heavy shadows, or loud animations.
6. **No AI-slop aesthetics:**
   - No uppercase labels (`uppercase`, `tracking-wide` / `tracking-wider` on UI text)
   - No gratuitous gradients on heroes, buttons, cards, or text
   - No glassmorphism / `backdrop-blur` / frosted panels
   - No sparkle/emoji decoration as UI ornament
   - No glow shadows, neon rings, or rainbow borders
   - No decorative icon next to every label
   - No stacked "AI" / "Pro" / "Beta" / "New" pills unless the state is load-bearing

If you catch yourself reaching for any of those, stop and use plain typography + spacing instead.

## Accessibility (non-negotiable)

- Correct semantic HTML and heading order (h1 → h2 → h3)
- Minimum contrast: 4.5:1 normal text, 3:1 large text/UI
- Visible `focus-visible` outlines on every interactive element
- Descriptive link text and `aria-label` for icon-only buttons
- Keyboard navigable and screen-reader friendly

## Stack-specific notes

Apply only the sections that match this repo.

### Tailwind

- Prefer existing utility patterns over new one-off class strings
- Don't increase font size for emphasis — use weight, color, or spacing
- Never animate width, height, margin, or padding

### React

Reuse existing components. Don't add a second component library.

```tsx
type ExportButtonProps = {
  onExport: () => void
}

export function ExportButton({ onExport }: ExportButtonProps) {
  return (
    <button type="button" onClick={onExport}>
      Export
    </button>
  )
}
```

- Clean up subscriptions, timers, and abort controllers in effect teardowns
- Pass data as props (or the project's existing data layer), not by poking the DOM
- Follow the file and naming conventions already in the UI folder

Vue, Svelte, Rails/Hotwire, and others: same rule — reuse primitives already in the repo.

## Quick checks

- Need emphasis? Weight or a token color already used in this app — never a bigger size
- Need status? Match existing status treatments; prefer plain text unless it must stand out
- Need decoration? Remove it. Ask: "Does this actually help the user?"
- New component? Find the closest existing screen and copy its structure
