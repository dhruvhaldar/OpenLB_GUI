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
