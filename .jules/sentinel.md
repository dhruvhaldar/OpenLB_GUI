## 2024-05-23 - Path Traversal in File Operations
**Vulnerability:** Use of `os.path.abspath(path).startswith(CASES_DIR)` allows sibling directory attacks (e.g., `/app/my_cases_secret` matches start of `/app/my_cases`).
**Learning:** String-based path validation is insufficient against path traversal and sibling attacks. `startswith` is particularly dangerous for paths.
**Prevention:** Use `pathlib.Path.resolve()` and `Path.is_relative_to()` to strictly validate path hierarchy. Always resolve paths to absolute forms before comparison.
