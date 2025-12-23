## 2024-05-23 - Async Action Feedback
**Learning:** Replacing blocking `alert()` dialogs with inline button state changes ("Saving..." -> "Saved!") significantly improves flow and perceived performance.
**Action:** Identify and replace all remaining blocking success alerts with inline status indicators or toast notifications.

## 2024-05-23 - Button Loading States
**Learning:** Users lack confidence in long-running processes (like "Build") without immediate visual feedback. Adding a spinner and changing text to present progressive tense (e.g. "Building...") provides necessary reassurance.
**Action:** Ensure all async action buttons have a distinct loading state with visual feedback.
