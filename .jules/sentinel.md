## 2024-05-23 - Path Traversal via String Prefix Matching
**Vulnerability:** The backend used `os.path.abspath(path).startswith(CASES_DIR)` to validate file access. This allowed access to sibling directories (e.g., `/app/data_secret` bypassing `/app/data`).
**Learning:** `startswith` is insufficient for path validation because it does not respect directory boundaries.
**Prevention:** Always use `pathlib.Path.resolve()` and `path.is_relative_to(base_dir)` to ensure the path is strictly within the allowed directory tree.
