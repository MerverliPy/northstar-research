# Remaining UI/UX Recommendations — Execution Plan

9 items, ordered by impact / effort ratio.

---

## 1. Sortable Tables

**Impact:** High — every CRUD view benefits immediately  
**Effort:** Medium — requires Table.tsx changes + column sort state

What:
- Click column header → sort ascending/descending/clear
- Sort arrow indicator (▲/▼) in active column header
- Client-side sort via `Intl.Collator` (numbers, dates, strings)
- Store sort state in a `useState<{key, dir}>` inside each CRUD view, passed to `<Table sortState onChangeSort>`

Files:
- `src/components/shared/Table.tsx` — add `sortState` + `onSort` props, render sort arrows, sort data internally
- All 5 CRUD views — pass sort state (no changes needed if Table handles internally)

---

## 2. Toast / Notification System

**Impact:** High — gives immediate feedback for every CRUD action  
**Effort:** Medium — new component + store

What:
- Global toast container in `App.tsx` or `MainPanel.tsx`
- Zustand `toastStore` with `toasts[]`, `addToast(msg, variant)`, `dismissToast(id)`
- Variants: success (green), error (red), info (blue)
- Auto-dismiss after 4s with fade-out animation
- Stack from bottom-right on desktop, bottom-center on mobile

Files:
- `src/stores/toastStore.ts` — new, ~30 lines
- `src/components/shared/Toast.tsx` — new, ~50 lines
- `App.tsx` — render `<ToastContainer />`
- All CRUD views — call `addToast('Project created', 'success')` in try/catch

---

## 3. Code Splitting (vis-network)

**Impact:** Medium — reduces initial bundle 354KB → ~150KB  
**Effort:** Low — `const vis = await import(...)` already in use

What:
- vis-network is already lazy-loaded (`await import('vis-network/standalone')`)
- Vite's chunk warning triggered because vis-data + vis-network combine to 650KB
- Move to `defineAsyncComponent` or keep dynamic import (already done)
- The actual work: configure Vite to split vis-network into its own chunk via `rollupOptions.output.manualChunks`

Files:
- `vite.config.ts` — add `build.rollupOptions.output.manualChunks`

---

## 4. Form Field Validation

**Impact:** Medium — guides users to fix errors before submit  
**Effort:** Medium — consistent helper across all modals

What:
- Inline error text below each field (red, `text-xs`)
- Validate on blur, clear on change
- Required fields: name, title
- Optional: URL format, character limits
- Pass error messages to `aria-describedby` on inputs

Files (per modal pattern):
- All 5 CRUD views — add `errors` state object, `validate(field)` function, error spans

Or create a lightweight hook:
- `src/hooks/useForm.ts` — new, ~40 lines
  - `useForm<T>(initial: T, validators: Record<keyof T, (v: any) => string | null>)`
  - returns `{ form, errors, setField, validateAll, isValid }`

---

## 5. Empty State Illustrations

**Impact:** Medium — onboarding warmth for every first-visit view  
**Effort:** Low-medium — SVG already done in polished views

What:
- Dashboard, all CRUD views, Graph, Cleanup, Import, Settings each have a distinct SVG illustration
- Most already done in Batch 4 (SVG inline icons for empty states)
- Enhance: add contextual subtitle text ("Create your first project to get started")

Files:
- Already polished in Batch 4. Minor text refinements only.

---

## 6. Lazy-Load Routes (View Code Splitting)

**Impact:** Medium — splits each view into own chunk  
**Effort:** Low — `React.lazy` + `Suspense` wrapper

What:
- Wrap each view in `React.lazy(() => import('./...View'))`
- Add `<Suspense fallback={<ViewSkeleton />}>` in router config
- Each view gets its own `.js` chunk (~20-60KB each)

Files:
- `router.tsx` — add `lazy()` wrappers
- Each view — export default instead of named export (or keep named + wrapper)

---

## 7. Dark/Light Theme Toggle

**Impact:** Medium — accessibility preference  
**Effort:** Medium — CSS variable swapping + store + toggle button

What:
- Tailwind `dark:` variant (already supported)
- Toggle in Settings or sidebar footer
- Persist in localStorage
- System preference detection via `prefers-color-scheme`

Files:
- `index.css` — light theme tokens
- `src/stores/themeStore.ts` — new, ~20 lines
- `Sidebar.tsx` or `SettingsView.tsx` — toggle button

---

## 8. Pagination Component

**Impact:** Medium — production-readiness for large datasets  
**Effort:** Medium-High — API + UI

What:
- Paged fetch (API already supports `limit` + `offset`)
- `Pagination` shared component: << < 1 2 3 ... > >>
- Per-page selector: 25 / 50 / 100
- Total count display: "Showing 1-25 of 143"

Files:
- `src/components/shared/Pagination.tsx` — new, ~80 lines
- `projectStore.ts` — add `offset` param, `total` state, `setPage()` action
- All CRUD views — wire pagination state

---

## 9. Keyboard Shortcuts / Command Palette

**Impact:** Low — power-user feature  
**Effort:** High — cross-cutting concern

What:
- `Cmd+K` → open command palette overlay
- Search for and navigate to any view, recent project, action
- Keyboard shortcut: `?` to show help modal
- `Escape` to close (already works for modals via Batch 1)

Files:
- `src/components/shared/CommandPalette.tsx` — new, ~150 lines
- `src/hooks/useKeyboardShortcut.ts` — new, ~30 lines
- `App.tsx` — render overlay

---

## Execution Order

| # | Item | Est. Time | Dependencies |
|---|------|-----------|--------------|
| 1 | Sortable Tables | 1h | Table.tsx already polished |
| 2 | Toast Notifications | 1.5h | New store + component |
| 3 | Form Validation Hook | 1h | New hook, wire 5 CRUD modals |
| 4 | Code Splitting (vis + routes) | 0.5h | vite.config + router.tsx |
| 5 | Pagination | 2h | Store + API + UI |
| 6 | Theme Toggle | 1.5h | CSS tokens + store |
| 7 | Command Palette | 2h | New complex component |

**Total:** ~9.5 hours. Items 1-4 are independent and can be parallelized by subagents.
