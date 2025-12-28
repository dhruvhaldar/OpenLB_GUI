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

## 2024-05-24 - Denial of Service via Config Read
**Vulnerability:** The `get_config` endpoint read arbitrary sized files into memory if they existed within the allowed directory. A large file (created externally or before limits) could cause OOM crashes.
**Learning:** Reading files into memory is dangerous even if the path is valid. File size must be checked before reading, or stream processing with limits must be used.
**Prevention:** Check `os.path.getsize()` before opening files for read, or use a streaming response with a maximum read limit. Added `X-Content-Type-Options: nosniff` as a defense-in-depth measure.

## 2024-05-24 - Resource Exhaustion via Concurrent Simulations
**Vulnerability:** The `/build` and `/run` endpoints allowed multiple concurrent executions of resource-intensive `make` commands. This could lead to server resource exhaustion (CPU/RAM DoS).
**Learning:** Even with timeouts, allowing unlimited concurrent heavy processes is a denial-of-service vector. Synchronous endpoints in threading-based servers (like Uvicorn/FastAPI default) run in parallel threads.
**Prevention:** Implement a global `threading.Lock` (or semaphore) to serialize or limit access to heavy resources. Reject excess requests with HTTP 409 (Conflict) to signal the client to wait.
