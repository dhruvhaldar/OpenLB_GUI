## 2026-01-20 - [MEDIUM] Preserve File Permissions in Configuration Save
**Vulnerability:** The application was resetting file permissions to 644 (world-readable) whenever `config.xml` was saved via the GUI, even if the user had explicitly restricted permissions (e.g., 600) to protect sensitive data.
**Learning:** Atomic writes (write-to-temp-then-rename) often inadvertently strip metadata like file permissions and ownership unless explicitly handled. Standard library tools like `tempfile` use default permissions that may be less secure than the original file.
**Prevention:** When performing atomic writes on existing files, always read the original file's `st_mode` (permissions) and apply it to the temporary file using `os.chmod` before replacing the original.

## 2026-02-16 - [MEDIUM] CSP Directives Hardcoded to Specific Ports
**Vulnerability:** The `Content-Security-Policy` `connect-src` directive in `index.html` was hardcoded to `http://localhost:8080`, causing the browser to silently block all API requests when the backend port changed. No error was visible in the UI — only "No cases found" appeared.
**Learning:** CSP violations fail silently from the user's perspective. The browser blocks the request and logs the error only in the DevTools console. This makes port mismatches between CSP policy and actual backend URLs extremely difficult to diagnose without checking DevTools.
**Prevention:** Keep CSP `connect-src` directives in sync with the backend API URL. Consider centralizing the port configuration in a single `.env` file or build-time variable that feeds both the CSP meta tag and the frontend `API_URL` constant.

## 2026-02-16 - [LOW] Port Conflicts with System Services
**Vulnerability:** Common development ports (8080, 8000) were silently occupied by other services (Node.js processes, Docker Desktop). The backend appeared to start successfully on the port, but another service was intercepting requests, returning unexpected responses (redirects, 404s).
**Learning:** On Windows, multiple services can attempt to bind the same port, and `netstat` may show multiple listeners. Docker Desktop is particularly aggressive about binding port 8000. Always verify the PID of the actual listener matches your expected process.
**Prevention:** Use less common ports (e.g., 3001) for development servers. Add a startup check that verifies the port is free before binding, or log the PID comparison to alert developers of conflicts.
