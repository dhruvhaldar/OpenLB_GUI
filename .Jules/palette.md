## 2025-05-20 - Native Dialogs Usage
**Learning:** The app relies on `window.confirm` and `window.prompt` for critical actions (Delete, Duplicate). These are blocking and often inaccessible or poor UX.
**Action:** Future enhancements should replace these with proper accessible modal components (e.g. using `<dialog>` or a custom component).

## 2025-05-21 - Destructive Action Focus Safety
**Learning:** Implicit `<dialog>` focus is unreliable for safety. Even `autoFocus` attribute can be flaky in React conditional rendering.
**Action:** Use `useRef` and `useEffect` with a small timeout to explicitly force focus on the "Cancel" button in destructive modals.
