# UI Polish Audit — Northstar Research Portal

**Date:** 2026-05-20  
**Scope:** `apps/research-portal/` — Jinja2+HTMX templates + React SPA  
**Design Doc:** `docs/DESIGN.md` (followed as reference)  
**Portal Port:** 3010  

---

## Summary

**Overall UI Polish Score: 62/100**

The React SPA side (chat, CRUD views, graph viewer, settings) is well-architected with a clear design system, shared components, and good PWA support. The Jinja2+HTMX side (legacy dashboard, quality, cleanup, extraction, graph viewer) lags significantly behind — lacking shared design tokens, missing loading/empty states, no focus management, and using a clashing light theme. The two UI layers coexist uneasily with duplicated routes and inconsistent experiences.

### Score Breakdown

| Category | Score | Notes |
|----------|-------|-------|
| Visual Design Quality | 58/100 | SPA strong, HTMX weak; hardcoded colors undermine theme system |
| Layout & Responsiveness | 68/100 | Sidebar auto-collapse works; no proper mobile nav; safe-area OK |
| Interaction Design | 55/100 | SPA has loading/empty states; HTMX has none; focus gaps |
| Dashboard UX | 60/100 | SPA dashboard OK; HTMX dashboard bare-minimum |
| Forms | 65/100 | Consistent SPA form patterns; HTMX forms don't exist |
| Design System | 65/100 | Good shared components in SPA; HTMX is independent silo; hardcoded colors |

---

## Top 5 Critical Findings

1. **CRITICAL — Two parallel UI systems with clashing visuals (score: 62 → blocked at 70).**
   The Jinja2+HTMX templates (`/dashboard`, `/quality`, `/cleanup`, `/extraction`, `/graph`) and the React SPA serve *the same routes* via server-side vs client-side routing but use completely different color palettes, typography, and component styles. Users get different experiences depending on whether they navigate via browser URL or SPA sidebar.
   
2. **HIGH — Hardcoded colors in SPA components defeat the CSS-variable theming system.**
   Button, Card, select elements, and text colors use Tailwind arbitrary values (`bg-[#16213e]`, `text-[#e94560]`) instead of `var(--color-northstar-*)` references. The light/dark theme toggle in the sidebar changes CSS variables but has no visual effect on most components because they ignore the variables.

3. **HIGH — No loading indicators for HTMX interactions.**
   The quality "Score" button, extraction "Extract" button, and cleanup "Execute Cleanup" button all trigger async operations with no visual feedback (`hx-indicator` not used). Users see no spinner, no disabled state, no skeleton — just a frozen UI until the response arrives.

4. **HIGH — Muted text contrast fails WCAG AA.**
   `#8888aa` on `#1a1a2e` background yields approximately 4.3:1 contrast ratio (below 4.5:1 minimum for small text). This affects all secondary text, placeholders, table headers, sidebar labels, and empty-state messages. The HTMX templates use `#888` on white and `#ccc` on dark nav — also failing.

5. **MEDIUM — No mobile navigation pattern below ~640px.**
   The sidebar auto-collapses to icons-only on narrow viewports, but there's no hamburger menu, no bottom tab bar, and no gesture support. On a phone in standalone PWA mode (no browser back button), users can't see navigation labels without expanding the sidebar, which pushes content off-screen.

---

## Visual Design Issues

| # | Issue | Severity | Location | Details |
|---|-------|----------|----------|---------|
| V1 | HTMX templates use light theme while SPA uses dark | CRITICAL | `templates/base.html` vs `spa/src/index.css` | `base.html`: `background: #f5f5f5`, `color: #333`. SPA: `background: #1a1a2e`, `color: #e0e0e0`. Completely different palettes |
| V2 | Hardcoded hex colors in SPA components bypass CSS variable theming | HIGH | `Button.tsx`, `Card.tsx`, all views | Button variants hardcode `bg-[#e94560]`, `bg-[#2a2a4a]` etc. Card variants hardcode `bg-[#16213e]`. Theme toggle has no effect |
| V3 | HTMX type scale not aligned with DESIGN.md | MEDIUM | `templates/base.html`, all HTMX templates | Headers use inline `font-size: 1.5rem` instead of Tailwind `text-xl`. Card values use `font-size: 2rem` instead of `text-3xl` |
| V4 | HTMX badge colors use Bootstrap-era palette | MEDIUM | `templates/base.html` lines 34-38 | `#d4edda`/`#155724` (green), `#fff3cd`/`#856404` (yellow) — does not match SPA's `bg-green-900/40 text-green-300` semantic colors |
| V5 | SPA stat card accent borders use `-mx-5 -mt-5` negative margins | MEDIUM | `DashboardView.tsx` line 46 | The colored top-border hack on stat cards uses negative margins to break out of the card's padding, creating brittle layout coupling between Card and DashboardView |
| V6 | No consistent border-radius token | LOW | Both systems | HTMX: `border-radius: 8px` on cards, `6px` on buttons. SPA: `rounded-lg` (8px) cards, `rounded-md` (6px) buttons. These happen to match but there's no single token |
| V7 | Sidebar brand "NORTHSTAR" only visible in expanded mode | LOW | `Sidebar.tsx` line 126 | Consistent with DESIGN.md but feels sparse when collapsed — no icon/brand mark |
| V8 | Accent gradient line on MainPanel clashes with dark background | LOW | `MainPanel.tsx` line 10 | The `from-[#e94560]/0 via-[#e94560]/50 to-[#e94560]/0` gradient line is barely visible on `#1a1a2e` background |

---

## Layout & Responsive Issues

| # | Issue | Severity | Location | Details |
|---|-------|----------|----------|---------|
| L1 | No mobile navigation pattern for touch devices | HIGH | `Sidebar.tsx` | Collapsed sidebar at ≤768px hides labels but navigation remains a narrow strip of bare icons — no hamburger, no bottom tabs, no swipe gestures |
| L2 | Duplicate route handling: HTMX server routes shadow SPA client routes | HIGH | `main.py` lines 77-81 vs `router.tsx` | Navigating to `/dashboard` in browser loads the HTMX template; navigating via SPA sidebar uses React Router client-side. Same URL, different UI |
| L3 | SPA main content has `overflow-hidden` on outer div, `overflow-y-auto` on inner | MEDIUM | `MainPanel.tsx` line 11 + all views | Double-scroll nesting; views manage their own scroll but `MainPanel` has `overflow-hidden` on `flex-1` — works but fragile |
| L4 | HTMX `container` has hardcoded `max-width: 1200px` | LOW | `templates/base.html` line 19 | No responsive max-width for small screens; content is cramped at 1200px full-width on mobile |
| L5 | Graph container uses `min-h-[500px]` but `flex-1` could cause layout shift | LOW | `GraphViewer.tsx` line 131 | When no project is selected, the empty state fills the remaining space; when graph loads, layout doesn't shift because `min-h-[500px]` + `flex-1` maintain consistent height |
| L6 | Safe-area applied to `html, body, #root` instead of only body | LOW | `spa/src/index.css` line 58 | Applying `env(safe-area-inset-*)` to `html` element can cause double-spacing in some browsers |
| L7 | Pagination wraps awkwardly on narrow screens | LOW | `Pagination.tsx` | The `flex-col sm:flex-row` layout is correct, but page numbers + page size selector can overflow on screens < 360px |
| L8 | Stat card grid `lg:grid-cols-5` forces 5 columns even with only 5 stat cards | LOW | `DashboardView.tsx` line 34 | The HTMX dashboard uses 4 cards (no Reports), SPA uses 5 — inconsistent column count |

---

## Interaction Design Gaps

| # | Issue | Severity | Location | Details |
|---|-------|----------|----------|---------|
| I1 | HTMX buttons have no loading indicators | CRITICAL | `quality.html`, `extraction.html`, `cleanup.html` | No `hx-indicator` attribute, no spinner element, no button disable during HTMX requests. Users can click "Score" multiple times |
| I2 | No debounce or loading state on HTMX "Execute Cleanup" | HIGH | `cleanup.html` line 34-42 | `hx-post` fires immediately on click; no `hx-indicator` for feedback during the potentially long operation |
| I3 | HTMX empty states are bare text only | HIGH | All HTMX templates | "No projects yet." (gray text), "No sources found." (gray text) — no icons, no CTAs, no contextual guidance |
| I4 | SPA `select` elements lack focus-visible ring consistency | MEDIUM | All SPA select elements | Selects have `focus:border-[#e94560]` but no outline ring, while inputs/buttons get the global `focus-visible: outline-2` from `index.css` |
| I5 | Modal close doesn't warn about unsaved form data | MEDIUM | All CRUD views | Clicking backdrop or Escape when a create/edit form has unsaved input silently discards changes |
| I6 | Copy button in MessageBubble has delayed opacity transition | LOW | `MessageBubble.tsx` line 31 | `opacity-0 group-hover:opacity-100` — the Copy button appears on hover but has no keyboard-accessible alternative |
| I7 | "Thinking" empty message bubble shows static "Thinking..." text | LOW | `MessageBubble.tsx` line 73 | When assistant message has empty content, it shows italic "Thinking..." with no animation, confusing users during SSE streaming |
| I8 | SPA toast animations use inline `style={{ animation: '...' }}` which can't be controlled by `prefers-reduced-motion` | LOW | `Toast.tsx` line 42 | The `slideIn`/`fadeOut` keyframe animations are hardcoded; no `@media (prefers-reduced-motion)` fallback |

---

## Dashboard UX Audit

### Chat View (`/`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Empty state | Good | Suggestion pills are excellent; welcome message sets expectations |
| Streaming UX | Good | ThinkingDots animation, tool result cards, message append |
| Input handling | Good | Enter to send, Shift+Enter newline, auto-resize textarea |
| Error recovery | Medium | SSE errors append raw JSON to message; no retry button |
| Accessibility | Medium | Textarea has `aria-label`; send button missing explicit label |

**Issues:**
- When `isStreaming` is true but no thinking text or actions are shown, there's zero visual feedback
- No cancel/stop button during streaming
- Suggestions don't update based on database state (always the same 5)

### Dashboard (`/dashboard`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Stat cards | Good | Color-coded top accent borders work well; skeleton loading |
| Recent projects | Adequate | Clean list but no status badges, no click-to-navigate |
| HTMX version | Poor | 4 stat cards, no Reports, no loading state, bare table |

**Issues:**
- SPA version: Recent projects list shows no project status badges
- No "View all projects" link from the recent projects section
- HTMX version: Shares same URL, completely different (inferior) experience

### CRUD Views (`/projects`, `/sources`, `/entities`, `/claims`, `/reports`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Table | Good | Sortable columns, skeleton loading, empty state with CTA |
| Create flow | Good | Modal form with validation, loading state on submit |
| Delete flow | Medium | No confirmation dialog before delete |
| Filtering | Adequate | Project dropdown for Sources/Entities/Reports |
| Bulk actions | Missing | No select-all, no batch delete |

**Issues:**
- Delete buttons trigger immediately with no confirmation
- Sources/Reports require project selection before showing anything (no "all" view)
- Claims/Entities views have no project filter

### Graph Viewer (`/graph`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Empty state | Good | SVG graph icon + instructional text |
| Loading state | Good | Novel skeleton with circle nodes |
| Error state | Good | Error message + retry button |
| Interaction | Adequate | vis-network zoom/pan/drag; no legend for colors |
| HTMX version | Poor | Same functionality but lighter styling, no loading/error states |

**Issues:**
- No color legend to explain what each node color means (Project=red, Source=blue, etc.)
- HTMX version (different route `/graph` via HTMX templates) duplicates functionality
- Graph doesn't resize when sidebar collapses/expands (no ResizeObserver)

### Cleanup (`/cleanup`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Safety gate UX | Good | Clear warning banner when disabled, button disabled |
| Stat cards | Good | Orphaned count, enabled status, overall status |
| Entity list | Adequate | Shows orphaned entities with type badges |
| HTMX version | Poor | Same data but no entity list, no suggestions, no safety banner detail |

**Issues:**
- HTMX version: Cleanup report is just a summary string + stats, no entity details
- No progress indicator during cleanup execution
- Results shown as raw JSON with no structured display

### Import Bridge (`/import`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Table | Good | Status badges colored by state, promote/delete actions |
| Batch promote | Good | Button shows count, loading state |
| Empty state | Adequate | Text only, no CTA or illustration |

**Issues:**
- Result display is raw JSON with no formatting
- No feedback when bridge API is unreachable (silent catch)
- Import form doesn't validate content length

### Settings (`/settings`)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Safety gates display | Good | Clear ENABLED/DISABLED with colored dot + badge |
| Service endpoints | Adequate | Monospace URLs, no copy buttons |
| Missing gates | Medium | "Promotion Enabled" gate from DESIGN.md not shown |

**Issues:**
- No copy-to-clipboard button for endpoint URLs
- "About" card has hardcoded version string instead of reading from config
- No link to documentation or health endpoints

---

## Forms Audit

### SPA Forms (all CRUD modals)

| Aspect | Rating | Notes |
|--------|--------|-------|
| Input consistency | Good | All inputs share same Tailwind classes: `bg-[#1a1a2e]`, `border-[#2a2a4a]`, `focus:border-[#e94560]` |
| Label quality | Good | All inputs have `<label htmlFor>` |
| Error display | Good | Red border + error text below, `aria-invalid` + `aria-describedby` |
| Validation timing | Adequate | Errors clear on change, only shown after `validateAll()` on submit — no real-time validation |
| Submit feedback | Good | Button shows spinner + disables, success/error toasts |
| Cancel behavior | Adequate | Closes modal, loses unsaved input |

**Issues:**
- ClaimsView confidence slider is visually nice but hard to use precisely on touch devices
- No `autofocus` on first field when modal opens
- The input CSS is repeated identically across 5 view files — no shared `<FormField>` component

### HTMX Forms

**No forms exist in HTMX templates.** All interactions are button posts. No validation.

---

## Design System Audit

### Strengths

1. **CSS custom properties defined** (`index.css` lines 3-44) with light and dark theme tokens
2. **Tailwind `@theme` directive** maps CSS vars to Tailwind utility names
3. **Shared SPA components** (Button, Card, Badge, Table, Modal, Toast, Pagination) cover most needs
4. **DESIGN.md** is comprehensive and accurate for the SPA
5. **TypeScript types** are well-defined in `types/index.ts`

### Weaknesses

| # | Issue | Severity |
|---|-------|----------|
| D1 | No shared `<FormField>` component — input+label+error repeated 26 times across views | MEDIUM |
| D2 | No shared `<StatCard>` component — stat cards repeated in DashboardView and CleanupView | MEDIUM |
| D3 | `select` styling not extracted to a shared component — repeated classes across 7 views | MEDIUM |
| D4 | CSS variables exist but are unused by components (all colors hardcoded) | HIGH |
| D5 | HTMX templates are an entirely separate design system with no token sharing | CRITICAL |
| D6 | No design tokens file (JSON/YAML) — CSS vars only | LOW |
| D7 | No Storybook or component documentation beyond DESIGN.md | LOW |

---

## Quick Wins (1–2 hours each)

| # | Fix | Effort | Impact |
|---|-----|--------|--------|
| 1 | Add `hx-indicator` spinners to HTMX buttons in quality.html, extraction.html, cleanup.html | 30 min | HIGH — fixes #I1, #I2 |
| 2 | Add SVG icons + CTAs to HTMX empty states (dashboard, quality, extraction) | 30 min | HIGH — fixes #I3 |
| 3 | Add `<FormField>` shared component to reduce 26 repeated input blocks | 1 hr | MEDIUM — fixes #D1 |
| 4 | Add delete confirmation dialog to all CRUD views | 1 hr | MEDIUM — UX safety |
| 5 | Replace hardcoded `text-[#8888aa]` with a slightly lighter `#9696b9` (WCAG AA) | 30 min | HIGH — fixes contrast |
| 6 | Add color legend to Graph Viewer | 30 min | LOW — clarity |
| 7 | Add `aria-label="Send message"` to the chat send button | 5 min | LOW — a11y |
| 8 | Add cancel/stop button during chat streaming | 1 hr | MEDIUM — UX |

---

## Structural Issues (need design decisions)

| # | Issue | Recommendation |
|---|-------|---------------|
| S1 | Two parallel UI systems (HTMX + SPA) | Decide: either retire HTMX templates and route everything through SPA, or unify styling and keep both. The SPA is clearly the primary UI — HTMX templates should be removed or migrated to SPA views |
| S2 | CSS variables defined but unused | Either make components consume `var(--color-northstar-*)` throughout, or remove the theme toggle and CSS variable system. Currently it's dead code |
| S3 | Light theme is defined but unreachable | If light theme is desired, refactor all hardcoded colors. Otherwise remove `:root` tokens and `.dark` overrides |
| S4 | No mobile navigation pattern | Consider a bottom tab bar (like PWA apps), a hamburger menu, or a slide-over drawer for mobile |
| S5 | Missing "Promotion Enabled" gate in Settings | Add third gate to SettingsView or remove from DESIGN.md |
| S6 | Graph viewer route conflict (`/graph` served by both HTMX and SPA) | The `/graph` HTMX template at `visual.router` prefix `/visual` doesn't conflict, but `/graph/data/{id}` in main.py is a raw endpoint. Remove the HTMX `/graph` path or route to SPA |

---

## PWA-Specific Findings

The PWA implementation is **solid** (well above average for this score range):
- ✅ Manifest with name, icons (192, 512, maskable), theme/background colors
- ✅ Service worker with Workbox precaching + runtime NetworkFirst for /api/*
- ✅ SW update detection with "Reload" toast via `usePWA` hook
- ✅ OfflineBanner component detects online/offline
- ✅ Safe-area padding on root elements
- ✅ Standalone display mode configured

**Minor PWA gaps:**
- No `apple-touch-icon` link in the SPA HTML (manifest handles it but iOS needs explicit link)
- No splash screen configuration for iOS (missing `apple-mobile-web-app-status-bar-style` meta in SPA index.html)
- Offline API caching strategy (NetworkFirst, 5-min TTL) may serve stale data without clear indication
- Install prompt button in sidebar has no visual prominence (hidden at bottom of sidebar)

---

## Accessibility Quick Hit List

| # | Issue | Fix |
|---|-------|-----|
| A1 | `#8888aa` text on `#1a1a2e` fails WCAG AA (4.5:1) | Lighten to `#9696b9` (5.0:1 ratio) |
| A2 | Chat send button has no accessible name | Add `aria-label="Send message"` |
| A3 | No `prefers-reduced-motion` support for animations | Wrap toast/skeleton animations in `@media (prefers-reduced-motion: no-preference)` |
| A4 | Copy button in MessageBubble is mouse-only | Add keyboard-accessible copy trigger |
| A5 | HTMX templates have no focus-visible outlines | Add `:focus-visible` styles to HTMX `base.html` |
| A6 | Confidence slider in ClaimsView has no accessible value display | The label shows value but no `aria-valuenow` on the range input |
| A7 | Graph viewer has no keyboard navigation support | vis-network supports keyboard but no instructions given |

---

## Files Changed in This Audit

*No files changed — this is an audit document only.*

A subsequent implementation pass should address the findings above, starting with the Quick Wins and working toward the Structural Issues.

---

## Remaining Recommendations

1. **Run automated contrast checks** on all color pairs using axe-core or Lighthouse
2. **Test on actual mobile devices** (not just responsive viewport in DevTools), especially in standalone PWA mode
3. **Consider adding end-to-end tests** (Playwright) for critical flows: chat → extract → view graph
4. **Add a component library tool** (Storybook or Ladle) to document and visually test shared components
5. **Define a strict color token usage lint rule** to prevent future hardcoded hex values in components
