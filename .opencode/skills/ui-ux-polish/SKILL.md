---
name: ui-ux-polish
description: Improve existing frontend interfaces using product-design, UX, accessibility, and visual-design best practices.
compatibility: opencode
---

Use this skill when improving an existing UI.

Checklist:
- Read DESIGN.md, README, package files, and relevant UI components.
- Identify the framework and styling system.
- Preserve app logic.
- Improve visual hierarchy.
- Improve spacing rhythm.
- Improve typography scale.
- Improve color usage and contrast.
- Improve responsive layout.
- Improve forms, buttons, cards, tables, modals, navigation, and empty/loading/error states.
- Check accessibility: semantic HTML, labels, keyboard focus, ARIA only where needed.
- Avoid over-animation.
- Avoid changing unrelated files.
- Run lint/build/typecheck when available.

- ## PWA-specific UI/UX checklist

When the project is a Progressive Web App or DESIGN.md describes a PWA, also evaluate:

- Mobile-first layout quality
- Desktop/tablet/mobile responsiveness
- Touch-friendly tap targets
- Safe-area spacing for mobile devices
- Standalone app experience
- App-shell layout and navigation
- Install prompt UX, if present
- Offline state UI
- Reconnection state UI
- Loading and skeleton states
- Cached-content messaging
- Empty/error states that work offline
- Native-app-like navigation patterns
- Avoiding browser-dependent UI assumptions
- Consistent theme color usage
- Manifest-driven branding alignment
- App icon and splash-screen consistency
- Performance-sensitive UI decisions
- Reduced layout shift
- Accessibility on small screens
- Keyboard and screen-reader usability

Do not modify service worker, manifest, caching strategy, or install behavior unless the user explicitly asks for PWA functionality changes.

If PWA files are present, inspect but treat carefully:
- manifest.json
- public/manifest.json
- service-worker.js
- sw.js
- next-pwa config
- vite-pwa config
- public/icons
- app metadata files
