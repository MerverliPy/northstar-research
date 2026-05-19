---
name: pwa-readiness
description: Audit and improve React/Vite progressive web apps for installability, offline UX, manifest quality, service-worker behavior, mobile usability, and app-like polish.
compatibility: opencode
---

## Use this skill when

The project is a PWA, uses vite-plugin-pwa, has a web manifest, uses a service worker, or DESIGN.md describes an installable app-like experience.

## Checklist

Inspect:

- package.json
- vite.config.ts
- index.html
- src/main.tsx
- src/App.tsx
- router files
- app shell/layout components
- public icons
- manifest configuration
- service-worker or Workbox configuration
- offline/update UI components if present

Evaluate:

- manifest name, short_name, description, theme_color, background_color, display, start_url, scope, and icons
- service-worker registration/update UX
- offline state handling
- reconnect handling
- cached API behavior
- mobile-first layout
- safe-area spacing
- touch target size
- standalone display mode assumptions
- navigation that works without browser chrome
- loading, empty, and error states
- reduced layout shift
- accessibility on small screens

Do not modify:

- caching strategy
- service-worker behavior
- manifest behavior
- API runtime caching

unless the user explicitly asks for PWA functionality changes.

Final output:

- PWA risks found
- UI/UX issues found
- safe improvements made
- manual browser checks still required
