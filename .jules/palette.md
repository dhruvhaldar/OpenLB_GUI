# Palette's Journal - Critical Learnings

## 2025-10-27 - Semantic Lists for Navigation
**Learning:** Using `div` soup for navigation lists (like case sidebars) is a common pattern that fails screen reader users, who rely on `list` and `listitem` roles to know "item 1 of 5".
**Action:** Always use `ul/li` for collections of items, even if they are styled as buttons or cards. Ensure the `ul` is labeled via `aria-labelledby` if a visible heading exists.

## 2025-10-27 - Empty States in Lists
**Learning:** Returning `null` or an empty `div` when a list is empty leaves users wondering if the app is broken or just empty.
**Action:** Always implement a specific "empty state" list item (e.g., `<li>No items found</li>`) inside the `ul` so the container structure remains consistent and informative.
