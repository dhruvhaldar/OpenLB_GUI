# Palette's Journal

## 2024-01-01 - Example Entry
**Learning:** Users often miss error messages at the top of the form.
**Action:** Move validation feedback inline or use a sticky notification toast.

## 2024-05-22 - Dynamic Button Feedback
**Learning:** Icon-only buttons that change state (like "Copy") need dynamic ARIA labels and titles to convey success/loading states to both screen readers and tooltips. Static labels like "Copy output" are confusing when the visual icon becomes a Checkmark.
**Action:** Always update `aria-label` and `title` when the button's visual state or icon changes.
