## 2024-05-23 - React.memo and Callback Stability
**Learning:** `React.memo` is ineffective if props (especially callbacks) are not stable. Using `useCallback` is essential when passing functions to memoized components. However, this introduces a dependency chain that strict linters (`react-hooks/exhaustive-deps`) will flag if not handled correctly.
**Action:** Always wrap handlers passed to memoized components in `useCallback`. Ensure all dependencies of that callback are also stable (or refs) to avoid breaking the memoization or the linter rules.
