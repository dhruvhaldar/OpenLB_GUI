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

## 2025-05-26 - Context-Aware Empty States
**Learning:** A single generic "No Selection" state is confusing when the data source itself is empty. Users need to know if they need to *create* data or just *select* it.
**Action:** Implement distinct empty states: 1) "No Data Found" with instructions on how to create/add data, and 2) "No Selection" with hints on how to select or search for existing data.
