# UI Polish Plan — Northstar Research Console

**Stack:** React 19 + TypeScript + Vite + Tailwind CSS v4 + PWA  
**Theme:** Dark (`#1a1a2e` bg, `#e94560` accent)  
**State:** Zustand stores  
**PWA:** vite-plugin-pwa, auto-update SW, NetworkFirst API cache  

**Last updated:** All Batches Completed

---

### Issue Catalog (15 areas across 17 files)

| Area | Severity | Files |
|------|----------|-------|
| **Accessibility** | High | Sidebar.tsx, Modal.tsx, GraphViewer.tsx, Table.tsx |
| **Empty states** | High | Table.tsx, all CRUD views, ChatView.tsx, DashboardView.tsx |
| **Loading states** | High | GraphViewer.tsx, CleanupView.tsx, ImportView.tsx, all CRUD |
| **Input styling** | Medium | ChatInput.tsx, all Modal form inputs, select dropdowns |
| **Sidebar icons** | Medium | Sidebar.tsx (emojis → SVG icons), collapsed aria-labels |
| **Card interactions** | Medium | Card.tsx (no hover shadow/transform), Dashboard stat cards |
| **Modal focus trap** | Medium | Modal.tsx (no focus trapping, no body scroll lock) |
| **Button variants** | Medium | Button.tsx (disabled states, loading spinner, icon support) |
| **Chat empty state** | Low | ChatView.tsx (emoji icon, plain suggestion pills) |
| **Message bubbles** | Low | MessageBubble.tsx (no timestamps, no copy action) |
| **Dashboard stat cards** | Low | DashboardView.tsx (no colored accent bars, no icons) |
| **Result card header** | Low | ResultCard.tsx (minimal header, no icon per tool type) |
| **PWA polish** | Low | index.html (no splash meta tags), no install prompt UI |
| **Safe-area spacing** | Low | index.css (no `env(safe-area-inset-*)` for mobile) |
| **Focus-visible rings** | Medium | Global (no custom focus-visible, Tailwind default only) |

---

## Batch 1 — Shared Components Foundation ✅

| File | Changes | Why | Status |
|------|---------|-----|--------|
| `index.css` | Add `scrollbar-gutter: stable`, `text-balance`, `focus-visible` ring tokens, `env(safe-area-inset-*)` padding, skeleton animation, overscroll-behavior | Prevent layout shift, polish typography, mobile safe-area, accessible focus, loading skeletons | ✅ |
| `Button.tsx` | Add `loading` prop with spinner SVG, `icon` mode, `active` state colors | Needed across CRUD views for async actions | ✅ |
| `Card.tsx` | Add `hover:shadow-lg hover:shadow-[#e94560]/5`, `hover:-translate-y-0.5`, `variant` prop (default/surface/bordered), `hover` prop | Makes cards interactive, improves visual depth | ✅ |
| `Modal.tsx` | Add focus trap, `aria-modal`, `role="dialog"`, body scroll lock, backdrop-blur, focus restore | Critical accessibility + UX polish | ✅ |
| `Badge.tsx` | Add `dot` prop for colored dot variant | Subtle inline status indicators | ✅ |
| `Table.tsx` | Add `loading` prop (skeleton rows), `emptyAction`, `stickyHeader`, hover all rows, rich empty state with SVG icon | Most-used component — loading + rich empty states | ✅ |

---

## Batch 2 — Layout + Navigation ✅

| File | Changes | Why | Status |
|------|---------|-----|--------|
| `Sidebar.tsx` | Replace emoji with SVG icons, `aria-label` on collapsed links, tooltip via `title`, left-border active indicator | Emojis inconsistent across platforms, inaccessible; SVGs crisp everywhere | ✅ |
| `MainPanel.tsx` | Add subtle accent gradient bar, `bg-[#1a1a2e]` on main, nested overflow container | Consistent app shell, polish accent line at top | ✅ |

---

## Batch 3 — Chat View ✅

| File | Changes | Why | Status |
|------|---------|-----|--------|
| `ChatView.tsx` | Replace emoji with SVG sparkle icon, suggestion pill hover with border accent, refined px-6 spacing | Polished first-impression empty state | ✅ |
| `ChatInput.tsx` | Rounded-full send button with arrow icon, textarea auto-resize (2-6 rows), useCallback for handleSend | Better input UX, modern send button | ✅ |
| `MessageBubble.tsx` | Copy button on hover, timestamp display, group-hover opacity transitions | Usability: copy results, see time | ✅ |
| `ResultCard.tsx` | Colored dot status via Badge dot prop, tool-colored left border strip (blue/purple/green/cyan), header bg | Visual hierarchy: distinguish tool results at a glance | ✅ |
| `ThinkingDots.tsx` | Opacity gradient on dots (80/60/40%), slower animation, pulse on text | Softer, more professional thinking indicator | ✅ |

---

## Batch 4 — View Pages ✅

| File | Changes | Why | Status |
|------|---------|-----|--------|
| `DashboardView.tsx` | Loading skeleton grid, accent-colored top border strip on stat cards, empty state SVG icon | More engaging dashboard | ✅ |
| `ProjectsView.tsx` | Table loading skeleton via store, empty state with action button, submitting state on modal, placeholder styling | Better UX on slow connections | ✅ |
| `SourcesView.tsx` | Table loading skeleton, SVG empty state, placeholder styling, submitting state | Consistent with ProjectsView | ✅ |
| `EntitiesView.tsx` | SVG empty state, placeholder styling, submitting state | Consistent pattern | ✅ |
| `ClaimsView.tsx` | Custom styled confidence slider track (red→yellow→green gradient), percentage display in badge | Intuitive confidence visualization | ✅ |
| `ReportsView.tsx` | SVG empty state, placeholder styling, submitting state | Pattern consistency | ✅ |
| `GraphViewer.tsx` | Skeleton graph (simulated node circles), error state with retry button, SVG empty state insight icon | Major visual gap resolved — no longer just text | ✅ |
| `CleanupView.tsx` | Warning banner with icon + description, loading skeleton stat cards, SVG empty states, entity hover bg | Professional admin tool feel | ✅ |
| `ImportView.tsx` | Loading skeleton (3 rows), result banner with dismiss button, consistent modal styling | Consistent with other views | ✅ |
| `SettingsView.tsx` | SVG section icons (shield/server/info), styled toggle pills with colored dot, monospace URLs, v0.2.0 | Engaging settings with visual sections | ✅ |

---

## Batch 5 — PWA + Meta Polish ✅

| File | Changes | Why | Status |
|------|---------|-----|--------|
| `index.html` | `apple-mobile-web-app-capable`, `status-bar-style=black-translucent`, `viewport-fit=cover` | Better iOS PWA experience, full-bleed notch support | ✅ |
| `index.css` | Safe-area padding via `env(safe-area-inset-*)`, `overscroll-behavior: none` (already in Batch 1) | Prevent overscroll in standalone PWA, notch safe area | ✅ |

---

### Files NOT Changed

- Stores: `chatStore.ts`, `projectStore.ts`, `settingsStore.ts`
- Hooks: `useSSE.ts`, `useAPI.ts`
- Types: `index.ts`
- Router: `router.tsx`
- PWA core: `vite.config.ts` (manifest, SW, caching strategy)
- Backend: any Python files

### Checks

```bash
cd apps/research-portal/research_portal/spa
npm run lint
npx tsc -b
npm run build
```
