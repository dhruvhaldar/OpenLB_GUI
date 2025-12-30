# Palette's Journal - Critical Learnings

## 2025-02-12 - Sidebar Semantics
**Learning:** Using semantic `<aside>` and `<nav>` elements for the sidebar improves accessibility structure, but requires careful handling of flexbox properties (`flex-col`, `overflow-y-auto`) to ensure proper scrolling behavior when the list is long, while keeping the header fixed.
**Action:** When refactoring sidebars, always check `overflow` behavior with large datasets and verify landmarks.
