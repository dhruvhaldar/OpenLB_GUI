## 2025-12-22 - Path Traversal in Backend
**Vulnerability:** The backend was using `startswith` to validate that file paths were within `CASES_DIR`. This allowed path traversal (e.g., accessing a sibling directory `my_cases_secret` if `CASES_DIR` was `my_cases`).
**Learning:** String-based path validation is error-prone. Even if `abspath` is used, simple prefix matching is insufficient because `/foo/bar_suffix` starts with `/foo/bar`.
**Prevention:** Use `pathlib.Path.resolve()` to canonicalize paths and `is_relative_to()` (available in Python 3.9+) to robustly check if a path is inside another.
