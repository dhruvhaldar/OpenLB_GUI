## 2026-01-06 - Rate Limiter Bypass Mitigation
**Vulnerability:** The rate limiter relied on a hardcoded allowlist of paths (e.g., `/build`, `/run`). This pattern is fragile because new sensitive endpoints might be forgotten, and path manipulation (e.g., `//build` depending on normalization) could potentially bypass the check.
**Learning:** Allow-lists for security controls on specific paths are prone to "Maintenance Oversight" and normalization bypasses.
**Prevention:** Switch to a "Secure by Default" Generic Rule. Apply controls based on the HTTP Method (POST, PUT, DELETE, PATCH) which covers *all* state-changing operations automatically, regardless of the path.
