## 2024-05-23 - Replacing Blocking Alerts with Inline Feedback
**Learning:** Users perceive blocking alerts (window.alert) as disruptive and "error-like" even for success states. Inline feedback (loading spinners, success checkmarks) provides a smoother, non-interruptive flow that feels more professional and integrated.
**Action:** Always prefer inline status indicators or toast notifications over window.alert for async operation feedback. Use temporary success states (e.g., "Saved!" for 2s) to confirm actions without requiring user dismissal.
