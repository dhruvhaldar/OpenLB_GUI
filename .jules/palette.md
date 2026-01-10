# Palette's Journal

## 2024-01-01 - Example Entry
**Learning:** Users often miss error messages at the top of the form.
**Action:** Move validation feedback inline or use a sticky notification toast.

## 2024-05-22 - Dynamic Button Feedback
**Learning:** Icon-only buttons that change state (like "Copy") need dynamic ARIA labels and titles to convey success/loading states to both screen readers and tooltips. Static labels like "Copy output" are confusing when the visual icon becomes a Checkmark.
**Action:** Always update `aria-label` and `title` when the button's visual state or icon changes.

## 2024-05-23 - Async Action Feedback
**Learning:** Destructive or complex actions (like Delete/Duplicate) often feel broken if they use blocking alerts/prompts without immediate UI feedback on the trigger element. The UI freezes or seems unresponsive until the native dialog appears or the operation completes.
**Action:** Use inline loading states (spinners) on the trigger button itself *before* and *during* the async operation, even if using native dialogs, to bridge the gap between user intent and system response.

## 2024-05-24 - Context-Aware Empty States
**Learning:** When filtering a list, the empty state must distinguish between "no items exist" (collection empty) and "no items match" (filter too strict). Using a generic "No items" message during filtering can confuse users into thinking data is missing.
**Action:** Always implement two distinct empty states for filtered lists: one for the zero-data state and one for the zero-results state.
