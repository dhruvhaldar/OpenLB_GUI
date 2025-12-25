## 2024-05-23 - Path Traversal in File Operations
**Vulnerability:** Use of `os.path.abspath(path).startswith(CASES_DIR)` allows sibling directory attacks (e.g., `/app/my_cases_secret` matches start of `/app/my_cases`).
**Learning:** String-based path validation is insufficient against path traversal and sibling attacks. `startswith` is particularly dangerous for paths.
**Prevention:** Use `pathlib.Path.resolve()` and `Path.is_relative_to()` to strictly validate path hierarchy. Always resolve paths to absolute forms before comparison.

## 2024-05-23 - Denial of Service via Config Upload
**Vulnerability:** The `save_config` endpoint accepted unlimited string content, allowing a malicious user to fill the disk by sending a massive payload, leading to Denial of Service.
**Learning:** Pydantic models by default validate types but not content constraints (like length). Explicit validators are needed for resource protection.
**Prevention:** Use Pydantic's `@field_validator` or `constr` (constrained string) to enforce maximum length limits on all user-supplied content that is stored or processed. Added logging to better monitor such attempts.

## 2024-05-23 - Denial of Service via Subprocess Timeout
**Vulnerability:** The `/build` and `/run` endpoints executed `subprocess.run` without a `timeout` argument. A malicious or buggy simulation case could hang indefinitely, tying up server resources and leading to Denial of Service.
**Learning:** External process execution in synchronous endpoints must always have a timeout to prevent infinite blocking.
**Prevention:** Always pass the `timeout` argument to `subprocess.run`, catch `subprocess.TimeoutExpired`, and handle the error gracefully to ensure server availability.
