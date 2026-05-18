# Northstar Research Console — Design

**URL:** `http://<host>:3011`  
**Stack:** React 18 + TypeScript + Vite + Tailwind CSS  
**Pattern:** Single Page Application (PWA) served by FastAPI  

---

## Visual System

### Palette

| Token | Value | Usage |
|-------|-------|-------|
| `northstar-dark` | `#1a1a2e` | Page background, deepest layer |
| `northstar-surface` | `#16213e` | Cards, panels, message bubbles |
| `northstar-border` | `#2a2a4a` | Borders, dividers |
| `northstar-accent` | `#e94560` | Primary actions, active nav, highlights |
| `northstar-text` | `#e0e0e0` | Body copy |
| `northstar-muted` | `#8888aa` | Secondary text, placeholders |

### Semantic Colors

| Token | Background | Text | Border |
|-------|-----------|------|--------|
| Success | `bg-green-900/40` | `text-green-300` | `border-green-700` |
| Warning | `bg-yellow-900/40` | `text-yellow-300` | `border-yellow-700` |
| Danger | `bg-red-900/40` | `text-red-300` | `border-red-700` |
| Info | `bg-blue-900/40` | `text-blue-300` | `border-blue-700` |

### Typography

- **Font stack:** `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- **Scale:** Tailwind defaults (`text-xs` through `text-3xl`)
- **Headers:** `font-bold text-white`, sizes `text-sm` (section) / `text-lg` (panel) / `text-xl` (page)
- **Body:** `text-sm text-[#e0e0e0]`
- **Muted:** `text-xs text-[#8888aa]`
- **Code:** `font-mono` (result cards, JSON output)

### Spacing

- **Page padding:** `p-6` (1.5rem)
- **Card padding:** `p-5` (1.25rem)
- **Gap between cards:** `gap-4` (1rem)
- **Table cells:** `px-3 py-2.5`

### Radius & Depth

- **Cards:** `rounded-lg` + `border border-[#2a2a4a]`
- **Buttons:** `rounded-md` (default), `rounded-full` (pills/suggestions)
- **Badges:** `rounded-full`
- **Modals:** `rounded-lg` + `shadow-xl` + backdrop `bg-black/60`

---

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│ ┌──────────┐ ┌────────────────────────────────────────────┐ │
│ │          │ │  Header bar (border-b)                      │ │
│ │ Sidebar  │ │  ┌────────────────────────────────────────┐ │ │
│ │          │ │  │                                        │ │ │
│ │  💬 Chat │ │  │  Active View                           │ │ │
│ │  📊 Dash │ │  │  (scrollable)                          │ │ │
│ │  📁 Proj │ │  │                                        │ │ │
│ │  📄 Srcs │ │  │                                        │ │ │
│ │  🏷  Ents │ │  │                                        │ │ │
│ │  📝 Clms │ │  └────────────────────────────────────────┘ │ │
│ │  📋 Rpts │ │  ┌────────────────────────────────────────┐ │ │
│ │  🔗 Grph │ │  │  Input bar (Chat only, border-t)       │ │ │
│ │  🧹 Cln  │ │  └────────────────────────────────────────┘ │ │
│ │  📥 Imp  │ └────────────────────────────────────────────┘ │
│ │  ⚙️  Set  │                                                │
│ └──────────┘                                                │
└──────────────────────────────────────────────────────────────┘
```

- **Sidebar:** Fixed left, `w-56` (collapsible to `w-14`), `bg-[#0f0f23]`, `border-r border-[#2a2a4a]`
- **Main Panel:** Flex-1, overflows hidden, contains `<Outlet>` from React Router
- **Header:** `h-14`, `border-b border-[#2a2a4a]`, shows page title + contextual actions

### Sidebar Behavior

| State | Width | Content |
|-------|-------|---------|
| Expanded | `w-56` (224px) | Icon + label per nav item |
| Collapsed | `w-14` (56px) | Icon only, centered |

Toggle via `◀` / `▶` button in the sidebar header.

### Navigation

Active route highlighted with `bg-[#e94560]/10 text-[#e94560] border-r-2 border-[#e94560]`. Inactive routes: `text-[#8888aa] hover:text-white hover:bg-[#2a2a4a]/30`.

---

## Views

### 1. Chat (`/`) — Default

**Purpose:** Conversational AI interface. User types natural language, the orchestrator LLM interprets intent and executes platform operations via SSE streaming.

**Layout:**
```
┌────────────────────────────────────┐
│ AI Research Assistant    [+ New Chat] │ ← header
├────────────────────────────────────┤
│                                    │
│  [AI] Hello! I can search, extract,│
│       score, manage your research. │ ← empty state
│                                    │
│  [Suggestions: "List projects" ...]│ ← suggestion pills
│                                    │
│  [User] Find sources about...      │ ← user bubble (right, #e94560)
│                                    │
│  [AI]  Thinking…                   │ ← streaming indicator
│  ┌──────────────────────────┐      │
│  │ Vector Search  completed │      │ ← result card
│  │ Found 3 matching results │      │
│  └──────────────────────────┘      │
│                                    │
├────────────────────────────────────┤
│ [textarea                    Send] │ ← input bar
│ Enter to send · Shift+Enter newline│
└────────────────────────────────────┘
```

**Message Bubbles:**
- **User:** Right-aligned, `bg-[#e94560] text-white rounded-lg`, avatar circle "U"
- **Assistant:** Left-aligned, `bg-[#16213e] border-[#2a2a4a] rounded-lg`, avatar circle "AI"
- **System:** Centered, `text-xs text-[#8888aa] bg-[#2a2a4a]/30 rounded-full`

**Result Cards:** Inline below assistant messages. Header bar shows tool name + status badge. Body shows data preview in monospace.

**Thinking Indicator:** Three bouncing dots (`#e94560`) with optional text.

**Input Bar:** Multi-line textarea (2 rows), send button. Disabled during streaming.

### 2. Dashboard (`/dashboard`)

**Purpose:** System-wide statistics and recent activity overview.

**Layout:**
```
┌────────────────────────────────────┐
│ Dashboard                          │
├────────────────────────────────────┤
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌─────┐│
│ │Proj 5│ │Srcs 12│ │Ents 8│ │Clms ││  ← stat cards (2-5 column grid)
│ └──────┘ └──────┘ └──────┘ └─────┘│
│                                    │
│ Recent Projects                    │
│ ┌────────────────────────────────┐ │
│ │ Project A          2026-05-15  │ │  ← list items
│ │ Project B          2026-05-12  │ │
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

### 3. CRUD Views (`/projects`, `/sources`, `/entities`, `/claims`, `/reports`)

**Purpose:** Manual create/read/update/delete for each entity type.

**Pattern:**
- **Header:** "Projects" + [ + New Project ] button
- **Filter bar (Sources/Entities/Reports):** Project dropdown selector
- **Data table:** Sortable columns with inline edit/delete actions
- **Create/Edit modal:** Form fields, Cancel + Create/Update buttons

**Projects** supports Edit (inline form modal).  
**Sources** requires project selection before listing.  
**Claims** includes a confidence slider (0-1) in the create modal.

### 4. Graph Viewer (`/graph`)

**Purpose:** Interactive Neo4j knowledge graph visualization.

**Layout:**
```
┌────────────────────────────────────┐
│ Graph Viewer    [Project ▼ select] │
├────────────────────────────────────┤
│                                    │
│   vis-network canvas (min-h 500px) │  ← color-coded nodes
│   • Project = red                  │  ← force-directed layout
│   • Source  = blue                 │
│   • Entity  = green                │
│   • Claim   = yellow               │
│   • Report  = purple               │
│                                    │
└────────────────────────────────────┘
```

**Interaction:** Hover tooltips, drag nodes, zoom/pan via vis-network.

### 5. Cleanup (`/cleanup`)

**Purpose:** Orphaned entity detection and gated destructive cleanup.

**Layout:**
```
┌────────────────────────────────────┐
│ Cleanup                            │
├────────────────────────────────────┤
│ [!] Destructive cleanup is disabled│ ← warning banner (if gated)
│                                    │
│ ┌───────────┐ ┌─────────┐ ┌──────┐│
│ │Orphaned 3 │ │Cleanup  │ │Status││  ← stat cards
│ └───────────┘ │ No      │ │Ready ││
│               └─────────┘ └──────┘│
│                                    │
│ [Refresh Report] [Execute Cleanup] │  ← actions
│                                    │
│ Orphaned Entities                  │
│ ┌────────────────────────────────┐ │
│ │ Entity A  (person)    abc123… │ │
│ │ Entity B  (concept)   def456… │ │
│ └────────────────────────────────┘ │
└────────────────────────────────────┘
```

**Safety:** Execute button disabled when `ENABLE_DESTRUCTIVE_CLEANUP=false` or no orphans exist.

### 6. Import Bridge (`/import`)

**Purpose:** Stage chat transcripts for promotion into research sources.

**Layout:**
```
┌────────────────────────────────────┐
│ Chat Import Bridge  [+Paste] [Promote All (3)]│
├────────────────────────────────────┤
│ ┌──────┬──────┬──────────┬───────┐│
│ │Title │Type  │Status    │Actions││  ← table
│ │Chat1 │paste │pending   │Promote││
│ │Chat2 │paste │promoted  │Delete ││
│ └──────┴──────┴──────────┴───────┘│
└────────────────────────────────────┘
```

**Promotion:** Single or batch (all pending). Markdown export available via bridge API.

### 7. Settings (`/settings`)

**Purpose:** Read-only view of safety gates and service configuration.

**Layout:**
```
┌────────────────────────────────────┐
│ Settings                           │
├────────────────────────────────────┤
│ Safety Gates                       │
│ ┌────────────────────────────────┐ │
│ │ Force Graph Extraction  DISABLED│ │  ← gate status
│ │ Destructive Cleanup     DISABLED│ │
│ └────────────────────────────────┘ │
│                                    │
│ Service Endpoints                  │
│ ┌────────────────────────────────┐ │
│ │ Research Agent   127.0.0.1:8099│ │  ← endpoint info
│ │ Chat Import Brg  127.0.0.1:3022│ │
│ │ Log Level        INFO          │ │
│ └────────────────────────────────┘ │
│                                    │
│ About                              │
│ v0.2.0 · PWA with PostgreSQL,     │
│ Neo4j, Ollama                      │
└────────────────────────────────────┘
```

---

## Shared Components

| Component | Props | Purpose |
|-----------|-------|---------|
| `Button` | `variant` (primary/secondary/danger/ghost), `size` (sm/md/lg) | Consistent button styles across all views |
| `Card` | `children`, `className`, `onClick?` | Container with surface background + border |
| `Badge` | `variant` (green/yellow/red/blue/gray) | Status pills (scores, states, types) |
| `Table` | `columns[]`, `data[]`, `keyField`, `onRowClick?` | Generic data table with typed column rendering |
| `Modal` | `open`, `onClose`, `title`, `children` | Overlay dialog with Escape-to-close |

---

## State Management

**Zustand stores** (lightweight, no boilerplate):

| Store | Key State | Purpose |
|-------|-----------|---------|
| `chatStore` | `messages[]`, `isStreaming`, `thinkingText`, `currentActions[]` | SSE streaming chat state |
| `projectStore` | `projects[]`, `sources[]`, `entities[]`, `claims[]`, `reports[]`, `stats` | CRUD entity cache + API calls |
| `settingsStore` | `settings`, `loading` | Safety gate status from `/api/settings` |

---

## Data Flow

```
User types in ChatInput
  → chatStore.sendMessage()
  → POST /api/chat/orchestrate?message=...   (SSE)
  → Orchestrator (Python backend)
     → LLM (Ollama qwen3:14b) classifies intent
     → Executes tools via httpx to Agent (8099) or Bridge (3022)
     → Streams SSE events: thinking → action → result → done
  → useSSE hook parses events
  → chatStore updates messages incrementally
  → MessageBubble / ResultCard re-render

Manual CRUD:
  → projectStore.createProject() (etc.)
  → fetch /api/v1/projects/ (proxied by portal to agent)
  → projectStore state updates
  → Table re-renders
```

---

## PWA Characteristics

| Feature | Implementation |
|---------|---------------|
| **Installable** | `manifest.webmanifest` with name "Northstar Research Console", theme `#1a1a2e`, accent `#e94560` |
| **Offline shell** | Service worker precaches HTML/CSS/JS via workbox |
| **API caching** | Runtime `NetworkFirst` strategy for `/api/*` (100 entries, 5-min TTL) |
| **Icons** | 192×192 and 512×512 PNG |
| **Auto-update** | `registerType: 'autoUpdate'` — new SW activates on reload |
| **Secure context** | Required for full PWA features (crypto, SW registration); falls back gracefully |

---

## Responsive Behavior

- Sidebar collapses to icon-only at narrow widths
- Stat card grid: `grid-cols-2 md:grid-cols-3 lg:grid-cols-5`
- Tables scroll horizontally on overflow
- Graph viewer fills available space (min-height: 500px)
- Modals constrain to `max-w-lg` on mobile

---

## Accessibility

- All interactive elements are keyboard-focusable
- Modals close on Escape
- Color alone is never the only indicator (text labels accompany badges)
- `role` attributes on interactive custom components
- Focus outlines preserved (Tailwind default)

---

## Browser Support

Targets all modern browsers. Falls back gracefully:
- `crypto.randomUUID()` → Math.random UUID generator (for HTTP contexts)
- `fetch` + `EventSource` (native APIs, no polyfills)
- CSS Grid + Flexbox (no float layouts)
