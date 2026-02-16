## 2026-01-20 - [MEDIUM] Preserve File Permissions in Configuration Save
**Vulnerability:** The application was resetting file permissions to 644 (world-readable) whenever `config.xml` was saved via the GUI, even if the user had explicitly restricted permissions (e.g., 600) to protect sensitive data.
**Learning:** Atomic writes (write-to-temp-then-rename) often inadvertently strip metadata like file permissions and ownership unless explicitly handled. Standard library tools like `tempfile` use default permissions that may be less secure than the original file.
**Prevention:** When performing atomic writes on existing files, always read the original file's `st_mode` (permissions) and apply it to the temporary file using `os.chmod` before replacing the original.
