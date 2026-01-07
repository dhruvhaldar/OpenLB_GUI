# Palette's Journal

## 2024-01-01 - Example Entry
**Learning:** Users often miss error messages at the top of the form.
**Action:** Move validation feedback inline or use a sticky notification toast.

## 2024-05-22 - Dynamic Button Feedback
**Learning:** Icon-only buttons that change state (like "Copy") need dynamic ARIA labels and titles to convey success/loading states to both screen readers and tooltips. Static labels like "Copy output" are confusing when the visual icon becomes a Checkmark.
**Action:** Always update `aria-label` and `title` when the button's visual state or icon changes.

## 2024-05-22 - Empty State Guidance
**Learning:** Empty states are dead ends if they don't provide a path forward. Replacing "No results" with actionable instructions (e.g., "Add files to X folder") transforms a confused user into an empowered one.
**Action:** Always include "next steps" or "how to fix" instructions in empty states, especially when the action (like creating files) happens outside the UI.
