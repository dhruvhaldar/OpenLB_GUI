## 2024-05-23 - [Path Traversal in Path Validation]
**Vulnerability:** The application used `path.startswith(CASES_DIR)` to validate if a path was within the allowed directory. This allowed path traversal to sibling directories sharing the same prefix (e.g., `my_cases` vs `my_cases_secret`).
**Learning:** String-based path validation is error-prone. `startswith` does not respect path delimiters.
**Prevention:** Use `pathlib.Path.resolve()` to canonicalize paths and `is_relative_to()` (Python 3.9+) to securely check path containment. Always treat paths as objects, not strings.
