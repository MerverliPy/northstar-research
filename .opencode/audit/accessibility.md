# Northstar Research Portal — Accessibility Audit Report

**Audit date:** 2026-05-20
**Scope:** `apps/research-portal/` — Jinja2+HTMX templates, React SPA, static assets, CSS, service worker
**Reviewer:** Accessibility Auditor agent
**Standard:** WCAG 2.1 Level AA

---

## Summary

| Metric | Value |
|--------|-------|
| **Overall health score** | **46 / 100** |
| Components reviewed | 30 |
| CRITICAL findings | 6 |
| HIGH findings | 8 |
| MEDIUM findings | 14 |
| LOW findings | 7 |

**Assessment:** The portal has solid foundations in some areas — good form labeling with `aria-invalid`/`aria-describedby`, well-structured focus trapping in modals, `role="alert"` on the offline banner, and proper `aria-live` regions on toast notifications. However, fundamental keyboard-navigation and screen-reader gaps across both the Jinja2 templates and the React SPA drag the score down significantly. The vis-network graph visualization, clickable table rows, chat suggestion buttons, and missing skip-navigation links are the most serious problems. The HTMX integration lacks any `aria-live` announcement mechanism for dynamic DOM updates, creating a silent experience for assistive-technology users.

---

## Detailed Findings

### CRITICAL (blocks core access for keyboard-only / screen-reader users)

| # | File | Lines | Issue | Severity | Recommendation |
|---|------|-------|-------|----------|----------------|
| C1 | `templates/base.html` | 47–60 | **No skip-to-content link.** Neither the Jinja2 templates nor the SPA provide a "skip to main content" mechanism. Keyboard users must tab through all navigation links on every page load. | **CRITICAL** | Add `<a class="skip-link" href="#main-content">Skip to content</a>` as the first focusable element in `<body>`, with CSS `:not(:focus):not(:active) { clip: rect(0 0 0 0); }` for off-screen hiding. |
| C2 | `spa/src/App.tsx` | 7–17 | **No skip-to-content link in SPA.** The React app root has no bypass mechanism. Combined with sidebar collapsed state (which hides link text), keyboard users face a long tab journey. | **CRITICAL** | Add a `<SkipLink />` component rendered as the first child in `<App>`, targeting `<main id="main-content">`. |
| C3 | `templates/graph_viewer.html` / `spa/src/components/graph/GraphViewer.tsx` | `graph_viewer.html:16,22–73` / `GraphViewer.tsx:156` | **vis-network canvas has no text alternative.** The graph is rendered on a `<canvas>` element (via vis-network) with zero accessible description. Screen-reader users get nothing. No `aria-label`, `aria-describedby`, `role="img"`, or fallback summary. | **CRITICAL** | Provide a sibling `<div class="sr-only" id="graph-summary" aria-live="polite">` that holds a plain-text graph description. After `loadGraph()`, populate it with e.g. "Graph loaded: N nodes, M edges showing Project X relationships. Node types: entities, sources, claims. Use the data table view for full access." Add `role="img" aria-label="Knowledge graph for project X" aria-describedby="graph-summary"` to the container. Offer a keyboard-navigable tabular alternative view of nodes/edges. |
| C4 | `spa/src/components/shared/Table.tsx` | 194–202 | **Clickable table rows have no keyboard support.** Row `onClick` handlers render the row as a `cursor-pointer` but omit `tabIndex={0}`, `role="button"` or `role="link"`, and keyboard event handlers (`onKeyDown` for Enter/Space). Keyboard-only users cannot activate row actions. | **CRITICAL** | When `onRowClick` is provided, set `tabIndex={0}`, `role="button"` (or `role="link"`), and add `onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onRowClick?.(item); } }}`. |
| C5 | `spa/src/components/chat/ChatView.tsx` | 189–197 | **Chat suggestion buttons are non-semantic, non-focusable `<button>` elements that lack proper grouping.** While these ARE `<button>` elements (good), they lack any grouping landmark or heading for the suggestions list. Additionally, each suggestion has no `aria-label` or `aria-describedby` to indicate it's a suggested prompt. | **CRITICAL** | Wrap the suggestions in a `<section aria-label="Suggested prompts">` with a heading. Ensure each button has a descriptive label via `aria-label="Ask: ${suggestion}"`. |
| C6 | `spa/src/components/chat/ThinkingDots.tsx` | 5–16 | **Loading animation has no accessible name or role.** The thinking/streaming indicator (three bouncing dots + text) is purely visual. Screen-reader users have no indication that the AI is "thinking." The outer container in ChatView also lacks `aria-live`. | **CRITICAL** | Add `role="status" aria-live="polite" aria-label="AI is thinking..."` to the ThinkingDots container. In ChatView, wrap the thinking indicator in an `aria-live="polite"` region. Respect `prefers-reduced-motion` by disabling the bounce animation. |

### HIGH (significant user-impact, needs attention)

| # | File | Lines | Issue | Severity | Recommendation |
|---|------|-------|-------|----------|----------------|
| H1 | `templates/base.html` | 47–60 | **Missing `<main>` landmark.** Both `div.container` and the `<body>` rely on generic `<div>` elements. No `<header>`, `<main>`, or `<footer>` landmarks exist. | **HIGH** | Change `div.container` to `<main id="main-content" class="container">`. Wrap the `<nav>` in a `<header>` element. |
| H2 | `templates/base.html` | 11–44 | **No heading hierarchy.** Pages start with `<h2>` as the top-level heading. There is no visually hidden `<h1>` for page identity. | **HIGH** | Add a consistent `<h1>` strategy: either use `<h1 class="sr-only">` for the site name, or ensure every page template renders an `<h1>` as its primary heading. Currently `dashboard.html`, `graph_viewer.html`, `extraction.html`, `cleanup.html`, and `quality.html` all use `<h2>`. |
| H3 | `templates/base.html` / `spa/src/index.css` / SPA buttons | `base.html:28–29` ; `CS: inset styling` | **Primary button color contrast failure.** White text (#ffffff) on `#e94560` background yields a contrast ratio of approximately **3.86:1**, which fails WCAG AA 4.5:1 for normal text (14px regular weight). | **HIGH** | Darken the primary button background to `#c7304f` (#c7304f → L≈0.15, contrast with white ≈4.9:1 — still borderline). Better: use `#b22234` or adjust text to a dark color on the accent background. Alternatively, increase font-size to 18.66px bold to qualify as "large text" (3:1 threshold). |
| H4 | `spa/src/components/chat/ChatView.tsx` | 156–219 | **No `aria-live` region for streaming chat.** When the AI streams responses via SSE (`thinking`, `action`, `result`, `done` events), there is no `aria-live` container announcing new content. Screen-reader users cannot perceive incremental updates. | **HIGH** | Wrap the message list in `<div role="log" aria-live="polite" aria-atomic="false">`. Announce new tool actions/results as they stream in with concise text descriptions. |
| H5 | `spa/src/components/Sidebar.tsx` | 138–171 | **Active nav link missing `aria-current="page"`.** The `NavLink` component from react-router-dom renders the link but does not set `aria-current="page"` on the active route. Screen readers cannot identify the current page. | **HIGH** | Add `aria-current="page"` to the `NavLink` render prop when `isActive` is true: `aria-current={isActive ? 'page' : undefined}`. |
| H6 | `spa/src/components/shared/Card.tsx` | 20–36 | **Interactive cards are not keyboard-accessible.** Cards with `onClick` handlers have `className="cursor-pointer"` but lack `tabIndex={0}`, `role="button"`, and keyboard event handlers. | **HIGH** | When `onClick` is provided: set `tabIndex={0}`, `role="button"`, `onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onClick?.(); } }}`. |
| H7 | `templates/cleanup.html` | 34–41 | **HTMX response injected into `<body>` without `aria-live`.** `hx-target="body" hx-swap="beforeend"` appends cleanup result HTML to `<body>`. No `aria-live` container is present, so the injected content is invisible to screen readers. | **HIGH** | Change to `hx-target="#cleanup-result"` and create a `<div id="cleanup-result" aria-live="polite">` container in the template. Ensure any appended HTML includes appropriate roles. |
| H8 | `spa/src/components/dashboard/DashboardView.tsx` | 44–51 | **Stat cards are informational-only but not structured for AT.** The stat cards (`Projects`, `Sources`, etc.) display numeric values with labels but use `<div>` elements without any `aria-labelledby` linking the label to the value. | **HIGH** | Add `role="region" aria-labelledby="stat-${s.label}"` to each stat `Card`. Set an `id` on the label element and reference it. This creates identifiable landmark regions for each stat. |

### MEDIUM (degrades experience, should be fixed)

| # | File | Lines | Issue | Severity | Recommendation |
|---|------|-------|-------|----------|----------------|
| M1 | `templates/base.html` | 51–56 | **Navigation does not use `aria-current`.** No `aria-current="page"` attribute on the active nav link, though the `active` CSS class is applied. | **MEDIUM** | Add `aria-current="page"` to the active `<a>` element. |
| M2 | `templates/dashboard.html`, `extraction.html`, `cleanup.html`, `quality.html` | Various | **Tables lack `<caption>` elements.** All data tables in Jinja templates are missing a `<caption>` for screen-reader context. | **MEDIUM** | Add `<caption class="sr-only">` to each `<table>`, e.g. "Recent Projects" or "Pending Extraction Sources". |
| M3 | `templates/extraction.html` | 39–46 | **HTMX Extract buttons lack status announcement.** When an extraction is triggered via HTMX and the row is swapped, there is no `aria-live` announcement of the result or loading state. | **MEDIUM** | Add `hx-indicator` to show a spinner, and wrap the table in an `aria-live="polite"` container. The HTMX response should include a status message for screen readers. |
| M4 | `templates/quality.html` | 35–41 | **HTMX Score buttons — same gap as extraction.** Score button responses are injected via HTMX `hx-swap="outerHTML"` with no accessible announcement. | **MEDIUM** | Same fix as M3: use an `aria-live="polite"` wrapper and include screen-reader-only status text in the HTMX response. |
| M5 | `spa/src/components/shared/Table.tsx` | 187–190, 32–45 | **Skeleton loading rows lack accessible labeling.** Loading skeletons have no `aria-busy` indicator, `aria-hidden`, or descriptive text. Screen-reader users hear nothing during data fetches. | **MEDIUM** | Add `aria-busy="true"` to the `<table>` element when loading, and include a visually-hidden `<caption>` that reads "Loading data…". Set `aria-hidden="true"` on each skeleton row. |
| M6 | `spa/src/components/shared/Modal.tsx` | 74–98 | **Root app content not hidden from screen readers when modal is open.** While `aria-modal="true"` is set on the dialog, the rest of the app (behind the backdrop) is not marked with `aria-hidden="true"` or `inert`. Screen readers may still navigate out of the modal. | **MEDIUM** | On modal open, set `aria-hidden="true"` on `#root` or the main content container. Restore on close. Alternatively, use the `inert` attribute on sibling content (browser support growing). |
| M7 | `spa/src/components/shared/Button.tsx` | 48–73 | **Loading state missing `aria-busy`.** When `loading={true}`, the button has no `aria-busy="true"` attribute. | **MEDIUM** | Add `aria-busy={loading ? true : undefined}` to the `<button>` element. |
| M8 | `spa/src/components/shared/Button.tsx` | 26, 55 | **Icon-only mode has no guaranteed `aria-label`.** The `icon` prop strips padding for icon-only buttons, but if callers forget to pass `aria-label`, the button is nameless. | **MEDIUM** | When `icon={true}`, require `aria-label` via TypeScript or add a runtime console warning. Consider a required `ariaLabel` prop for icon-only buttons. |
| M9 | `spa/src/components/shared/Pagination.tsx` | 50–118 | **Pagination not wrapped in `<nav>`.** The pagination controls are bare `<div>` elements without a `<nav>` landmark or `aria-label="Pagination"`. | **MEDIUM** | Wrap the pagination container in `<nav aria-label="Pagination">`. |
| M10 | `spa/src/components/chat/ChatView.tsx` | 38–40 | **Auto-scroll does not respect `prefers-reduced-motion`.** `scrollTo({ behavior: 'smooth' })` runs regardless of user motion preferences. | **MEDIUM** | Wrap in a media query check: `const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;` and use `behavior: prefersReducedMotion ? 'auto' : 'smooth'`. |
| M11 | `spa/src/components/shared/OfflineBanner.tsx` | 31 | **`animate-pulse` on status dot ignores reduced motion.** The offline banner's pulsing dot animates regardless of `prefers-reduced-motion`. | **MEDIUM** | Add `motion-safe:animate-pulse` (Tailwind class) or conditionally apply via CSS media query. |
| M12 | `spa/src/components/shared/Toast.tsx` | 40–43 | **Toast auto-dismiss is CSS-driven, not programmatic.** When toasts fade out via CSS animation after 4s, screen readers do not reliably detect removal. The `role="status"` container only announces additions, not removals. | **MEDIUM** | Use a programmatic dismissal with a `setTimeout` that calls `dismissToast()` rather than relying solely on CSS `animation: fadeOut`. This ensures the DOM change triggers the live region update. |
| M13 | `spa/src/router.tsx` | 7–24 | **`ViewSkeleton` fallback has no `aria-busy` or loading announcement.** Route-transition skeletons are purely visual with no screen-reader indication. | **MEDIUM** | Add `role="status" aria-live="polite" aria-label="Loading page…"` to the skeleton container. |
| M14 | `templates/graph_viewer.html` | 6–14 | **`<select>` element has `<label>` but no associated `aria-describedby` for the graph state.** When a project is selected, the graph loads but there is no announcement. | **MEDIUM** | Add an `aria-live="polite"` status region near the graph that updates with "Loading graph for project X…" and "Graph loaded: N nodes, M edges." |

### LOW (minor polish, non-blocking)

| # | File | Lines | Issue | Severity | Recommendation |
|---|------|-------|-------|----------|----------------|
| L1 | `templates/base.html` | 3–46 | **Missing `<meta name="description">`.** Neither the Jinja template nor the SPA includes a meta description. | **LOW** | Add `<meta name="description" content="Northstar Research Console — AI-powered research platform with PostgreSQL, Neo4j, and Ollama.">` to the `<head>`. (Already present in SPA `index.html` but missing from `base.html`.) |
| L2 | `templates/base.html` | 7–9 | **CDN scripts loaded without `integrity` or `crossorigin` attributes.** This is a supply-chain concern rather than an accessibility issue, but worth noting. | **LOW** | Add `integrity` hashes and `crossorigin="anonymous"` to all CDN `<script>` and `<link>` tags. |
| L3 | `spa/src/components/shared/Modal.tsx` | 80 | **Backdrop `<div>` has `onClick` but no `role`.** The backdrop is purely for mouse dismissal; Escape key is handled separately. This is usable but not ideal for screen-reader interaction. | **LOW** | Add `aria-hidden="true"` to the backdrop div since keyboard-only dismissal is handled via Escape. |
| L4 | `spa/src/components/chat/ChatInput.tsx` | 59–61 | **Hint text not linked to textarea.** The "Enter to send / Shift+Enter for newline" hint is in a `<p>` but not referenced from the textarea via `aria-describedby`. | **LOW** | Add `id="chat-hint"` to the `<p>` and `aria-describedby="chat-hint"` to the `<textarea>`. |
| L5 | `spa/src/components/chat/MessageBubble.tsx` | 60–61 | **Avatar initials "U"/"AI" are purely decorative but visible to screen readers.** These single-character labels are ambiguous in isolation. | **LOW** | Add `aria-label="User"` and `aria-label="AI Assistant"` to the avatar divs, or hide them with `aria-hidden="true"` and provide a text-visible role label in the bubble header. |
| L6 | `spa/src/components/shared/Table.tsx` | 49–50 | **`colSpan={99}` is a hack for EmptyState.** Should use `colSpan={columns.length}` to avoid spanning extra columns that don't exist. | **LOW** | Change to `colSpan={columns.length}`. |
| L7 | `static/manifest.webmanifest` | 1 | **Manifest is solid but could include a `categories` field and a 512px maskable icon with proper purpose.** Already has maskable icon. | **LOW** | Add `"categories": ["productivity", "utilities"]` for app store categorization. |

---

## Quick Wins (fixable in < 1 hour)

These items are high-impact and can be addressed rapidly:

1. **Add skip-to-content links** (C1, C2): ~15 min per template/app.
   ```html
   <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:bg-white focus:text-black focus:px-4 focus:py-2 focus:rounded">
     Skip to content
   </a>
   ```

2. **Fix heading hierarchy** (H2): ~20 min total. Replace `<h2>` with `<h1>` in each page template and in each SPA view component.

3. **Add `aria-current="page"` to nav links** (H5, M1): ~15 min. In Base template, add `aria-current` alongside the `active` class. In Sidebar.tsx, add `aria-current={isActive ? 'page' : undefined}` to NavLink.

4. **Add `<main>` landmark** (H1): ~5 min. Change `div.container` to `<main id="main-content" class="container">`.

5. **Add `aria-label` to icon-only buttons** (M8): ~10 min. Add a TypeScript type constraint or doc comment ensuring callers pass `aria-label`.

6. **Wrap pagination in `<nav>`** (M9): ~5 min.

7. **Fix `colSpan` hack in Table** (L6): ~1 min.

8. **Link hint text to textarea** (L4): ~5 min.

**Estimated total quick-win time: ~90 minutes.**

---

## Structural Issues (requiring design changes)

These items require cross-component refactoring or architectural decisions:

1. **Graph accessibility strategy** (C3): vis-network renders to `<canvas>`, which is inherently inaccessible. Options:
   - **Tabular fallback:** Offer a "View as table" toggle that renders nodes/edges as sortable data tables.
   - **Text summary:** Automatically generate a plain-text description of the graph structure after each load.
   - **Keyboard nav:** Allow node-by-node keyboard navigation with focus indicators (requires vis-network interaction event hooks).
   - **Sonification:** Not recommended for MVP.

2. **HTMX accessibility wrapper** (H7, M3, M4): All HTMX-powered interactions need a convention for `aria-live` announcements. Create a reusable pattern:
   ```jinja2
   <div id="htmx-response" aria-live="polite" aria-atomic="true">
     <!-- HTMX swaps happen inside here -->
   </div>
   ```
   Each HTMX response partial should include a `.sr-only` status message.

3. **Chat streaming announcements** (H4, C6): SSE-driven chat needs `aria-live` regions. The architecture should wrap the message list in `<div role="log" aria-live="polite">` and inject concise status text as messages stream. The `ThinkingDots` component needs a `role="status"` wrapper.

4. **Color system audit** (H3): The `#e94560` primary accent fails contrast with white text. Either:
   - Darken the accent color across all components.
   - Use dark text on the light version of the accent.
   - This requires CSS variable updates in both `index.css` (SPA) and `base.html` inline styles (Jinja).

5. **Keyboard-navigable interactive cards and table rows** (C4, H6): The Card and Table components need consistent keyboard interaction patterns. This requires updating the shared component API to enforce `role` and `tabIndex` when interactive handlers are provided.

6. **`prefers-reduced-motion` system** (M10, M11, C6): All animations (chat auto-scroll, toast slideIn/fadeOut, thinking dots, skeleton shimmer, offline banner pulse, stat card hover) need a centralized reduced-motion check. Consider a `useReducedMotion()` hook and a CSS class strategy.

---

## HTMX Usage Pattern Audit

| Pattern | File | Finding |
|---------|------|---------|
| `hx-post` + `hx-swap="outerHTML"` | `extraction.html:40-43`, `quality.html:35-39` | Works for sighted users; no `aria-live` container surrounding the table means screen readers don't announce the row swap. **Fix:** wrap table in `aria-live="polite"` div; include `.sr-only` status in HTMX response partial. |
| `hx-post` + `hx-target="body"` + `hx-swap="beforeend"` | `cleanup.html:34-41` | Injects results at end of `<body>`. Worst-case pattern — content is appended outside any landmark. **Fix:** target a dedicated `#cleanup-result` container with `aria-live="polite"`. |
| `hx-trigger="click"` no loading indicator | `extraction.html:43`, `quality.html:39`, `cleanup.html:38` | No `hx-indicator` to show loading state. Button state doesn't change until swap completes. **Fix:** add `hx-indicator="#spinner"` and a loading spinner element. |
| No `hx-on` for post-swap announcements | All HTMX usage | HTMX lacks a built-in accessible-announcement pattern. **Fix:** use `hx-on::after-request` to trigger a custom event that updates a shared `aria-live` region. |

---

## Keyboard Event Handler Audit

| File | Handler | Assessment |
|------|---------|------------|
| `Modal.tsx:16-44` | `handleKeyDown` for Escape + Tab trap | **Good.** Correctly traps focus and closes on Escape. |
| `Table.tsx:160-165` | `onKeyDown` for Enter/Space on column headers | **Good.** Sortable column headers are keyboard-operable. |
| `ChatInput.tsx:22-27` | `handleKeyDown` for Enter (send) / Shift+Enter (newline) | **Good.** Standard chat UX pattern. |
| `Table.tsx:194-202` | Row `onClick` with no `onKeyDown` | **MISSING.** (C4) |
| `Card.tsx:20-36` | Card `onClick` with no `onKeyDown` | **MISSING.** (H6) |
| `ChatView.tsx:189-197` | Suggestion buttons — native `<button>` with `onClick` | **OK.** Native `<button>` handles Enter/Space natively. |

---

## Screen Reader Compatibility Summary

| Feature | Status | Notes |
|---------|--------|-------|
| Page landmarks | ⚠️ Partial | `<main>` missing in Jinja; `<aside>` and `<nav>` present in SPA |
| Heading hierarchy | ❌ Broken | Pages start at `<h2>` instead of `<h1>` |
| Form labels | ✅ Good | All form inputs have `<label htmlFor>`, `aria-invalid`, `aria-describedby` for errors |
| Table semantics | ⚠️ Partial | Proper `<thead>/<tbody>/<th>`; missing `<caption>`; sortable headers have `aria-sort` |
| Dynamic content | ⚠️ Partial | Toasts have `aria-live`; chat streaming and HTMX swaps do not |
| Focus management | ⚠️ Partial | Modal focus trap works; no skip link; row/card click targets not focusable |
| Color contrast | ❌ Fail | Primary button fails WCAG AA; muted text borderline |
| Reduced motion | ❌ Missing | No motion preferences respected anywhere |
| Graph/visualization | ❌ Fail | Canvas-only with zero accessible alternative |

---

## PWA Accessibility Notes

The PWA implementation (`manifest.webmanifest`, `sw.js`, `usePWA.ts`) is solid for offline support. Key observations:

- **Service worker update toast** uses the accessible `ToastContainer` with `aria-live="polite"`. Good.
- **Manifest** includes `name`, `short_name`, `display: standalone`, `theme_color`, and `lang: "en"`. Good.
- **`theme-color` meta** has both light and dark variants. Good.
- **iOS PWA meta tags** (`apple-mobile-web-app-capable`, etc.) are present. Good.
- The **offline banner** uses `role="alert"` with proper ARIA. Good.
- **Missing:** No `categories` field in manifest. No `screenshots` for install prompts. (LOW)

---

## Tests / Manual Checks Recommended

1. **Keyboard-only navigation test:**
   - Tab through all pages (Jinja and SPA) — verify skip link, landmark navigation, modal focus trap, table row activation.
   - Verify `Tab` + `Shift+Tab` reverses through sidebar nav links.

2. **Screen-reader test (NVDA or VoiceOver):**
   - Navigate to Dashboard → verify stat cards announced as landmarks.
   - Open a modal → verify `aria-modal` prevents background navigation.
   - Trigger HTMX extraction → verify swap result is announced.
   - Use chat suggestions → verify each suggestion is clearly labeled.
   - Load a graph → verify text summary is announced.

3. **Contrast audit (automated):**
   - Run `axe-core` or Lighthouse on both `http://localhost:3010/` (Jinja) and the SPA routes.
   - Manually verify `#e94560` + white text combination.

4. **Reduced-motion test:**
   - Enable `prefers-reduced-motion: reduce` in OS settings.
   - Verify: chat auto-scroll is instant, thinking dots don't animate, toasts don't slide/fade, skeletons don't shimmer, offline pulse is static.

5. **Zoom test:**
   - Zoom to 200% on each view and verify no content is clipped or overlapping.

---

## Residual Risks

- **vis-network library:** This third-party canvas library does not expose accessible node data. Any text-alternative solution requires duplicating the underlying graph data into a parallel accessible DOM structure, which may drift out of sync.
- **HTMX + Alpine.js interaction:** Alpine's `@change` directives combined with HTMX swaps may create focus-order surprises. Manual testing with a screen reader after each swap is recommended.
- **React fast-refresh:** During development, component remounts may cause transient focus loss — this is not a production concern but may confuse keyboard-only testers during dev.
- **Chat SSE streaming:** If the AI returns very large tool-result data, the `aria-live` region may overwhelm the screen reader with verbose announcements. Consider a summarization strategy (e.g., "Search returned 42 results" instead of listing all results).

---

## Appendix: Color Contrast Calculations

| Foreground | Background | Ratio | WCAG AA (normal) | WCAG AA (large) |
|------------|-----------|-------|-------------------|-------------------|
| #ffffff (white) | #e94560 (accent red) | **3.86:1** | ❌ Fail (needs 4.5) | ❌ Fail (needs 3.0, but text is only 14px weight 500 — not "large") |
| #8888aa (muted) | #1a1a2e (dark bg) | ~5.4:1 | ✅ Pass | ✅ Pass |
| #e0e0e0 (text) | #16213e (surface) | ~11:1 | ✅ Pass | ✅ Pass |
| #e0e0e0 (text) | #1a1a2e (dark bg) | ~12:1 | ✅ Pass | ✅ Pass |
| #155724 (text) | #d4edda (green bg) | ~7.0:1 | ✅ Pass | ✅ Pass |
| #ccc (nav links) | #1a1a2e (nav bg) | ~8.9:1 | ✅ Pass | ✅ Pass |
| #ffffff (white) | #d63851 (hover red) | ~4.3:1 | ❌ Fail | ⚠️ Borderline |
| #ffffff (white) | #c7304f (suggested darker red) | ~4.9:1 | ✅ Pass | ✅ Pass |
