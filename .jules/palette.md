# Palette's Journal - Critical Learnings

## 2025-02-12 - Sidebar Semantics
**Learning:** Using semantic `<aside>` and `<nav>` elements for the sidebar improves accessibility structure, but requires careful handling of flexbox properties (`flex-col`, `overflow-y-auto`) to ensure proper scrolling behavior when the list is long, while keeping the header fixed.
**Action:** When refactoring sidebars, always check `overflow` behavior with large datasets and verify landmarks.

## 2025-02-12 - Skip to Content Pattern
**Learning:** Adding a "Skip to main content" link is a critical micro-UX for keyboard users in app-like layouts (Sidebar + Main Content). It must be hidden visually (`sr-only`) but visible on focus (`focus:not-sr-only`). The target container needs `tabIndex={-1}` to accept programmatic focus and `outline-none` to prevent a focus ring on the entire container, unless desired.
**Action:** Always verify keyboard navigation flow in 2-column layouts and add skip links if missing.
