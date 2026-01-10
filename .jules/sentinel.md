## 2024-05-20 - Baseline

## 2026-01-10 - Log Injection via User Input
**Vulnerability:** User input (`req.new_name`) was logged directly in `duplicate_case` before validation. An attacker could inject newlines to forge fake log entries (Log Injection / CWE-117).
**Learning:** Logging user input *before* validation or without sanitization (`repr()`) is a common trap, especially in "informational" logs. Naive automated tests might confirm a vulnerability even if it's fixed (escaped) if they just grep for the payload string.
**Prevention:** Always log user input *after* validation or wrap it in `repr()` to escape control characters. Verification scripts must check for structural injection (newlines), not just the presence of the payload string.
