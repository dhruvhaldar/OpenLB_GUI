## 2025-05-20 - Native Dialogs Usage
**Learning:** The app relies on `window.confirm` and `window.prompt` for critical actions (Delete, Duplicate). These are blocking and often inaccessible or poor UX.
**Action:** Future enhancements should replace these with proper accessible modal components (e.g. using `<dialog>` or a custom component).

## 2025-05-21 - Empty State Actions
**Learning:** Passive empty states (like "No output") in technical tools can leave users stranded.
**Action:** Always include primary action buttons (Build/Run) in empty states to reduce friction and guide the workflow.

## 2025-05-22 - Search-to-List Keyboard Navigation
**Learning:** Users searching in a sidebar often expect to jump immediately to results. Tabbing through search controls (like "Clear") breaks this flow.
**Action:** Implement `ArrowDown` in search inputs to directly focus the first result, and `Enter` to auto-select it, creating a "Command Palette" feel.

## 2025-05-23 - Contextual Control Availability
**Learning:** Persistent toolbars for content areas (e.g., LogViewer) clutter the UI when the content is empty.
**Action:** Explicitly disable and visually dim controls (Copy, Download, Clear) when their target content is missing to indicate unavailability and focus attention on primary actions.

## 2025-05-24 - Keyboard Shortcut Discoverability
**Learning:** Power users rely on keyboard shortcuts (Ctrl+B, Ctrl+Enter), but these are often hidden in tooltips, making them hard to discover.
**Action:** Add subtle visible hints (e.g., small `<kbd>` badges) directly within action buttons to teach users shortcuts without requiring them to hover or read documentation.

## 2025-05-25 - List Navigation Delegation
**Learning:** Managing keyboard navigation (Arrow keys) for dynamic lists is cleanest when delegated to the container (`ul`) rather than individual items.
**Action:** Attach `onKeyDown` to the parent container and use `document.activeElement` to determine the current focus index, simplifying state management and reducing event listeners.

## 2025-05-26 - Visual Shortcut Consistency
**Learning:** Adding visual keyboard shortcut hints (like `<kbd>`) to secondary action buttons (like Save) significantly improves feature discoverability and consistency when primary actions (Build, Run) already have them.
**Action:** Ensure all keyboard-accessible action buttons display their shortcuts inline when in an idle state, using consistent styling (e.g., `bg-white/10` for dark themes).

## 2025-05-27 - Dialog Accessibility Labeling
**Learning:** Native `<dialog>` elements do not automatically announce their heading content to screen readers upon opening.
**Action:** Always link the dialog container to its title using `aria-labelledby` and a unique ID (via `useId()`) to ensure the context is announced immediately.

## 2025-05-28 - List Count Visibility
**Learning:** Users often need immediate feedback on the scale of data or filter results. "Cases" alone is ambiguous; "Cases (10)" or "Cases (1/10)" provides crucial context.
**Action:** Append count badges to section headers for dynamic lists, using the format "(X/Y)" when filtered to show the relationship between the subset and the whole.

## 2025-05-29 - Empty State Keyboard Hints
**Learning:** Empty states are valuable real estate for teaching keyboard shortcuts that would otherwise be hidden.
**Action:** Use empty content areas to display prominent keyboard shortcut hints for initiating the primary workflow (e.g. search).

## 2025-05-30 - Main Content Loading States
**Learning:** During initial data fetch or refresh, showing a generic "No Selection" state while the sidebar is loading creates a disconnect and implies an actionable state that doesn't exist.
**Action:** Implement a dedicated, full-size loading state for the main content area that activates specifically when the data source is loading and no item is currently selected.

## 2025-05-31 - Code Editor Accessibility
**Learning:** Implementing "Tab" for indentation in textareas improves UX for developers but creates a keyboard trap.
**Action:** When trapping focus with Tab, strictly follow WCAG 2.1.2 by implementing an "Escape" hatch (blur) and providing visible and programmatic (aria-describedby) instructions.

## 2025-06-01 - Ambiguous List Items
**Learning:** In lists where items may have identical names but different contexts (e.g. same name in different domains), standard tooltips showing only the name fail to disambiguate.
**Action:** Enhance tooltips and `aria-label` attributes to include the full context (e.g. "Domain / Name") to prevent confusion for both mouse and screen reader users.

## 2025-06-02 - Focus Ring Contrast on Colored Backgrounds
**Learning:** Using a standard focus ring color (e.g., blue) on colored active states (like a blue selected list item or green primary button) fails accessibility contrast ratios.
**Action:** Conditionally swap the focus ring color to white (or a high-contrast alternative) when the element has a saturated background color.

## 2025-06-03 - Focus Restoration
**Learning:** When a focused element (like a Delete button) is removed from the DOM, focus reverts to the body, causing a loss of context for keyboard users.
**Action:** Detect when the active item is removed (e.g., via effect cleanup or state change) and programmatically move focus to a logical container (like the main content area or list).

## 2025-06-04 - Seamless Navigation Loop
**Learning:** Users searching in a sidebar expect to be able to "back out" of a list into the filter that created it using the arrow keys, not just Tab/Shift+Tab.
**Action:** Always check if a list component has a corresponding search/filter input and ensure ArrowUp/Down connects them bi-directionally.

## 2025-06-05 - Visual List Disambiguation
**Learning:** Relying solely on tooltips to disambiguate identical list items (e.g. same name, different parent) forces sighted users to hunt-and-peck.
**Action:** Display the distinguishing context (e.g. domain/parent folder) directly in the list item layout, using secondary text styling to maintain hierarchy without clutter.

## 2026-02-16 - Silent Network Failures
**Learning:** When API requests are blocked by CSP or CORS, the UI shows a generic "No cases found" empty state with no indication that a network error occurred. Users perceive this as "no data exists" rather than "data fetch failed", leading to confusion and misdiagnosis.
**Action:** Distinguish between "empty result" and "fetch error" states in the UI. Show a clear error banner with the failure reason (e.g., "Connection refused", "Blocked by security policy") and a retry button, rather than reusing the empty-state component for both scenarios.
