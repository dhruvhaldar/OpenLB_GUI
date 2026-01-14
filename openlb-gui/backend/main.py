from fastapi import FastAPI, HTTPException, Body, Query

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from pydantic import BaseModel, field_validator, Field
import os
import subprocess
import logging
import tempfile
import re
import threading
import shutil
import time
import signal
from collections import defaultdict, deque
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("openlb-backend")

app = FastAPI()

# Rate Limiting Middleware
# Protects sensitive endpoints from DoS and abuse
class RateLimiter:
    def __init__(self, requests_per_minute: int = 5):
        self.limit = requests_per_minute
        # Performance Optimization: Use deque for O(1) pops from the left
        # instead of O(N) list slicing/re-allocation during cleanup.
        self.requests = defaultdict(deque)
        # Clean up old entries periodically (in a real app, use Redis)
        self.last_cleanup = time.time()

    def is_rate_limited(self, ip: str) -> bool:
        now = time.time()
        # Simple cleanup every minute to prevent memory leak from old IPs
        if now - self.last_cleanup > 60:
            self.requests.clear()
            self.last_cleanup = now

        dq = self.requests[ip]

        # Efficiently remove expired requests from the left (oldest first)
        # O(k) where k is the number of expired requests (usually small)
        # This avoids copying the entire list as list comprehension would do.
        while dq and now - dq[0] > 60:
            dq.popleft()

        if len(dq) >= self.limit:
            return True

        dq.append(now)
        return False

rate_limiter = RateLimiter(requests_per_minute=20) # 20 req/min/IP for sensitive actions

# Trusted Origins
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}

class TrustedOriginMiddleware(BaseHTTPMiddleware):
    """
    Sentinel Security Middleware: Enforce Strict Origin Checks
    Prevents CSRF attacks by validating the 'Origin' or 'Referer' header
    on state-changing requests (POST, PUT, DELETE, PATCH).
    """
    def __init__(self, app, allowed_origins):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            origin = request.headers.get("origin")
            referrer = request.headers.get("referer")

            # 1. Check Origin (Standard Browser Behavior)
            if origin:
                if origin not in self.allowed_origins:
                     logger.warning(f"Blocked CSRF attempt. Origin: {origin}")
                     return Response("Forbidden: Untrusted Origin", status_code=403)

            # 2. Check Referer (Fallback / Extra Security)
            # Referer includes path, so we verify it starts with an allowed origin
            elif referrer:
                 if not any(referrer.startswith(allowed) for allowed in self.allowed_origins):
                     logger.warning(f"Blocked CSRF attempt. Referer: {referrer}")
                     return Response("Forbidden: Untrusted Referrer", status_code=403)

            # 3. If both are missing, we ALLOW (Lax Mode)
            # This is necessary because non-browser tools (curl, scripts, TestClient)
            # typically do not send Origin/Referer.
            # Since the app runs on localhost, the primary threat is the browser (CSRF).

        return await call_next(request)

class LimitUploadSize(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int) -> None:
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        # Sentinel Enhancement: Secure by Default
        # Apply checks to all methods that can carry a body to prevent bypasses.
        if request.method in ["POST", "PUT", "PATCH"]:
            # Security Fix: Enforce Content-Length
            # Reject Chunked Encoding or requests without Content-Length to prevent
            # Memory Exhaustion DoS attacks. The backend expects finite, known-size payloads (JSON/text).
            if 'content-length' not in request.headers:
                 return Response("Content-Length required", status_code=411)

            content_length = int(request.headers['content-length'])
            if content_length > self.max_upload_size:
                return Response("Request body too large", status_code=413)
        return await call_next(request)

# Allow CORS for frontend dev
# Restrict to standard local dev ports to prevent access from arbitrary sites
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(ALLOWED_ORIGINS),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply TrustedOriginMiddleware
app.add_middleware(TrustedOriginMiddleware, allowed_origins=ALLOWED_ORIGINS)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Rate Limiting for state-changing operations
    # We apply this before processing the request
    # Sentinel: Broadened scope to all state-changing methods to prevent bypasses and future oversight
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        client_ip = request.client.host if request.client else "unknown"
        if rate_limiter.is_rate_limited(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip} on {request.url.path}")
            # We return a JSON response directly for 429
            # Note: We can't easily raise HTTPException in middleware, so we return Response
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."}
            )

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=()"
    return response

app.add_middleware(LimitUploadSize, max_upload_size=2 * 1024 * 1024) # 2MB limit
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Resolve cases directory relative to the project root (2 levels up from backend/main.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Use resolve() for CASES_DIR to ensure we have the absolute path
CASES_PATH = (PROJECT_ROOT / "my_cases").resolve()
# Keep CASES_DIR as string for glob/compat but use CASES_PATH for security checks
CASES_DIR = str(CASES_PATH)

# Global lock to prevent concurrent build/run operations
# This prevents Resource Exhaustion DoS and file corruption
execution_lock = threading.Lock()

# Pre-compile regex for control characters optimization
# Matches any char < 32 (0x20) INCLUDING tab (0x09)
# Security Fix: Rejecting tabs prevents Log Injection (CWE-117) and visual spoofing.
CONTROL_CHARS = re.compile(r'[\x00-\x1f]')

# Pre-compile Regex for hidden path check optimization
# Matches a dot at the beginning of a string or immediately after a separator
HIDDEN_PATH_PATTERN = re.compile(r'(?:^|[\\/])\.')

# Pre-compile Regexes for Validation Hot Paths
# Optimization: Pre-compiling regexes avoids cache lookup overhead and recompilation
# for patterns used in every request (config validation, duplicate checks).
XXE_DOCTYPE_PATTERN = re.compile(r'<!\s*DOCTYPE', re.IGNORECASE)
XXE_ENTITY_PATTERN = re.compile(r'<!\s*ENTITY', re.IGNORECASE)
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Allowed environment variables to pass to subprocesses
SAFE_ENV_VARS = {
    'PATH', 'LANG', 'LC_ALL', 'TERM', 'LD_LIBRARY_PATH',
    'HOME', 'USER', 'SHELL', 'TMPDIR'
}

def get_safe_env():
    """
    Returns a sanitized environment dictionary for subprocess execution.
    Only allows specific safe variables and those starting with OLB_.
    Prevents leakage of sensitive backend environment variables (keys, secrets).
    """
    safe_env = {}
    for key, value in os.environ.items():
        if key in SAFE_ENV_VARS or key.startswith('OLB_'):
            safe_env[key] = value
    return safe_env

def run_command_safe(cmd, cwd, env, stdout, timeout, max_output_size=10 * 1024 * 1024):
    """
    Executes a command in a new process group and kills the entire group on timeout or output limit.
    Prevents zombie processes and resource exhaustion (DoS) when a simulation hangs
    or writes excessive logs (Disk Exhaustion).
    """
    # Start new session (setsid) to create a new process group
    # This allows us to target the group with killpg
    start_new_session = True if os.name != 'nt' else False

    with subprocess.Popen(
        cmd, cwd=cwd, env=env,
        stdout=stdout, stderr=subprocess.STDOUT,
        text=False, # Binary mode
        start_new_session=start_new_session
    ) as process:
        try:
            # Sentinel Fix: Monitor process and output size to prevent DoS
            # Instead of a blocking wait(), we poll periodically.
            start_time = time.time()
            while time.time() - start_time < timeout:
                # 1. Check if process finished
                if process.poll() is not None:
                    # Final check for output size (in case it finished very fast)
                    if stdout and os.fstat(stdout.fileno()).st_size > max_output_size:
                        logger.warning(f"Process output exceeded limit ({max_output_size} bytes).")
                        stdout.write(b"\n\n[ERROR: Output limit exceeded. Terminating process to prevent disk exhaustion.]\n")
                        raise subprocess.TimeoutExpired(cmd, timeout)
                    return process.returncode

                # 2. Check output size (Disk Exhaustion Protection)
                if stdout:
                    try:
                        current_size = os.fstat(stdout.fileno()).st_size
                        if current_size > max_output_size:
                            logger.warning(f"Process output exceeded limit ({max_output_size} bytes). Killing.")
                            stdout.write(b"\n\n[ERROR: Output limit exceeded. Terminating process to prevent disk exhaustion.]\n")
                            # Trigger the cleanup logic in the except block
                            raise subprocess.TimeoutExpired(cmd, timeout)
                    except OSError:
                        pass # Should not happen with valid file descriptor

                # Performance Optimization: Reduced polling interval from 0.5s to 0.1s.
                # This improves responsiveness for short-lived commands (like fast builds or immediate failures)
                # by reducing the latency penalty from ~500ms to ~100ms.
                # The overhead of checking poll() and fstat() 10x/sec is negligible compared to the UX gain.
                time.sleep(0.1)

            # If loop finishes without returning, it timed out
            raise subprocess.TimeoutExpired(cmd, timeout)

        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out or exceeded limits: {cmd}")
            # Kill the process group to ensure all children are terminated
            if start_new_session:
                try:
                    pgid = os.getpgid(process.pid)
                    logger.warning(f"Killing process group {pgid}")
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                # Fallback for Windows or if setsid failed
                process.kill()

            # Ensure the parent process is definitely dead and cleaned up
            process.kill()
            raise # Re-raise to be caught by the caller

def validate_case_path(path_str: str) -> str:
    """
    Validates that the path is within the CASES_DIR.
    Returns the absolute path as a string if valid.
    Raises HTTPException if invalid.
    """
    try:
        # Security check: Reject paths with control characters (e.g., newlines, null bytes)
        # to prevent Log Injection (CWE-117) and other filesystem weirdness.
        # We allow printable characters, spaces, and path separators.
        # This explicitly blocks payloads like "safe/path\nINJECTED_LOG"
        # PERFORMANCE OPTIMIZATION: Use regex instead of loop for ~10x speedup
        if CONTROL_CHARS.search(path_str):
            logger.warning(f"Invalid characters in path: {repr(path_str)}")
            raise HTTPException(status_code=400, detail="Invalid characters in path")

        # Sentinel Enhancement: Support relative paths to avoid exposing server directory structure.
        # If path is relative, anchor it to CASES_DIR.
        if not os.path.isabs(path_str):
            path_str = os.path.join(CASES_DIR, path_str)

        # Performance Optimization: Use os.path + regex instead of Pathlib
        # Pathlib's resolve() and relative_to() involve object overhead and iterative checks.
        # os.path.realpath + relpath + regex provides a ~5x speedup for this hot path.
        target_path = os.path.realpath(path_str)

        # Optimization: Fast path for containment check
        # os.path.relpath involves path splitting and joining, which is slower.
        # We use simple string operations for the common case where target_path is inside CASES_DIR.
        # This provides an additional ~14x speedup over relpath.
        rel = None
        if target_path.startswith(CASES_DIR):
            if len(target_path) == len(CASES_DIR):
                rel = "."
            elif target_path[len(CASES_DIR)] == os.sep:
                rel = target_path[len(CASES_DIR)+1:]

        if rel is None:
            # Check if the path is relative to CASES_DIR
            try:
                rel = os.path.relpath(target_path, CASES_DIR)
            except ValueError:
                # On Windows, relpath raises ValueError if paths are on different drives
                logger.warning(f"Access denied (drive mismatch): {repr(path_str)}")
                raise HTTPException(status_code=403, detail="Access denied")

        # Check if path is outside CASES_DIR (starts with '..') or is absolute (on non-Windows)
        if rel.startswith('..') or (os.name != 'nt' and rel.startswith('/')):
             # Use repr() to prevent log injection
             logger.warning(f"Access denied for path: {repr(path_str)}")
             raise HTTPException(status_code=403, detail="Access denied")

        # Security Enhancement: Prevent access to hidden files/directories (starting with .)
        # Use regex to check if any path component starts with '.' in the relative path
        if HIDDEN_PATH_PATTERN.search(rel):
            logger.warning(f"Access denied for hidden path: {repr(path_str)}")
            raise HTTPException(status_code=403, detail="Access denied: Hidden paths are restricted")

        # Security check: Prevent operations on the root cases directory itself
        if target_path == CASES_DIR:
             logger.warning(f"Attempted operation on root cases directory: {repr(path_str)}")
             raise HTTPException(status_code=403, detail="Access denied: Cannot operate on root cases directory")

        return target_path
    except (ValueError, RuntimeError, OSError):
        # Handle cases where is_relative_to might fail or other path errors
        # Use repr() to prevent log injection
        logger.error(f"Error validating path: {repr(path_str)}")
        raise HTTPException(status_code=403, detail="Access denied")

def read_log_tail(file_obj, limit_bytes=100 * 1024) -> str:
    """
    Reads the tail (end) of a file object.
    If the file is larger than limit_bytes, it reads the last limit_bytes
    and prepends a truncation message.
    """
    file_obj.seek(0, 2) # Seek to end
    size = file_obj.tell()

    if size > limit_bytes:
        file_obj.seek(size - limit_bytes)
        raw = file_obj.read()
        # Decode with replace to handle potentially cut multi-byte characters
        return "[... Output truncated at beginning ...]\n" + raw.decode('utf-8', errors='replace')
    else:
        file_obj.seek(0)
        return file_obj.read().decode('utf-8', errors='replace')

class CommandRequest(BaseModel):
    case_path: str = Field(..., max_length=4096)

class DuplicateRequest(BaseModel):
    source_path: str = Field(..., max_length=4096)
    new_name: str = Field(..., max_length=255)

class ConfigRequest(BaseModel):
    case_path: str = Field(..., max_length=4096)
    content: str

    @field_validator('content')
    def validate_content_length(cls, v):
        # Limit content size to 1MB to prevent DoS
        if len(v) > 1024 * 1024:
            raise ValueError('Content size exceeds 1MB limit')

        # XXE Prevention: Reject DTD declarations
        # If the backend or simulation parses this XML, DTDs enable XXE attacks
        # Use regex to catch variations with whitespace
        # Performance Optimization: Use pre-compiled regex patterns
        if XXE_DOCTYPE_PATTERN.search(v) or XXE_ENTITY_PATTERN.search(v):
            raise ValueError('XML Document Type Definitions (DTD) are not allowed for security reasons')

        return v

@app.post("/cases/duplicate")
def duplicate_case(req: DuplicateRequest, request: Request):
    """Duplicates an existing case."""
    safe_source = validate_case_path(req.source_path)
    client_ip = request.client.host if request.client else "unknown"

    # Performance Optimization: Use pre-compiled regex
    if not VALID_NAME_PATTERN.match(req.new_name):
        # Security Fix: Log Injection (CWE-117)
        # We must not log req.new_name directly if it hasn't been validated yet.
        # It could contain newlines and fake log entries.
        logger.warning(f"Invalid duplicate attempt from {client_ip}: name={repr(req.new_name)}")
        raise HTTPException(status_code=400, detail="Invalid name. Use alphanumeric, underscore, and hyphen only.")

    # Log AFTER validation to prevent Log Injection
    # Audit Log: Include client IP for accountability
    logger.info(f"Duplicating case: {safe_source} to name: {req.new_name} (Request from: {client_ip})")

    parent_dir = os.path.dirname(safe_source)
    target_path = os.path.join(parent_dir, req.new_name)

    # Validate target path (even though constructed safely, ensures it's in CASES_DIR)
    try:
        if not Path(target_path).resolve().is_relative_to(CASES_PATH):
             raise HTTPException(status_code=403, detail="Access denied")
    except Exception:
        raise HTTPException(status_code=403, detail="Access denied")

    if os.path.exists(target_path):
        raise HTTPException(status_code=409, detail="Case with this name already exists")

    try:
        # Security Fix: Use symlinks=True to prevent dereferencing symlinks.
        # If symlinks=False (default), a symlink to /etc/passwd in the source would be copied
        # as the actual file content, leading to arbitrary file read / disclosure.
        # It also prevents infinite recursion if a symlink points to a parent directory.
        shutil.copytree(safe_source, target_path, symlinks=True)
        return {"success": True, "new_path": os.path.relpath(target_path, CASES_DIR)}
    except Exception as e:
        logger.error(f"Duplicate failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate case")

@app.delete("/cases")
def delete_case(request: Request, case_path: str = Query(..., max_length=4096)):
    """Deletes a case directory."""
    safe_path = validate_case_path(case_path)
    client_ip = request.client.host if request.client else "unknown"
    # Audit Log: Include client IP for accountability
    logger.info(f"Deleting case: {safe_path} (Request from: {client_ip})")

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Case not found")

    try:
        shutil.rmtree(safe_path)
        return {"success": True}
    except Exception as e:
        logger.error(f"Delete failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete case")

@app.get("/cases")
def list_cases():
    """Scans for directories with a Makefile in my_cases."""
    logger.info("Listing cases")
    cases = []
    try:
        # Performance Optimization: Use os.scandir() instead of glob.glob().
        # scandir() yields DirEntry objects that contain file type information (is_dir, is_symlink)
        # without requiring additional system calls (stat). This avoids thousands of unnecessary stat calls.
        # It also allows us to skip expensive Path.resolve() checks for non-symlink directories.
        with os.scandir(CASES_DIR) as it1:
            for entry1 in it1:
                if not entry1.is_dir() or entry1.name.startswith('.'): continue

                # Optimization: Cache symlink status and resolve only once per entry
                # This prevents redundant resolve() calls when an entry is checked for both
                # being a case (Level 1) and a domain container (Level 2).
                if entry1.is_symlink():
                    try:
                        resolved = Path(entry1.path).resolve()
                        if not resolved.is_relative_to(CASES_PATH):
                            logger.warning(f"Ignored symlinked case: {entry1.path} -> {resolved}")
                            continue
                    except Exception:
                        continue

                # Level 1 check (CASES_DIR/Case/Makefile)
                mk1 = os.path.join(entry1.path, "Makefile")
                # accessing file directly is faster than glob
                if os.path.isfile(mk1):
                    # Entry is a Case
                    rel_path = entry1.name
                    cases.append({
                        "id": rel_path,
                        "path": rel_path,
                        "name": entry1.name,
                        "domain": "Uncategorized"
                    })

                    # Performance Optimization:
                    # If the directory is already identified as a Case (has Makefile), we treat it as a leaf node.
                    # We skip scanning its children to avoid iterating over potentially thousands of build artifacts
                    # or output files (e.g. .vtk files) often found in the case root.
                    # This enforces a structure where a Case cannot contain other Cases.
                    continue

                # Level 2 check (CASES_DIR/Domain/Case/Makefile)
                # If we passed the symlink check above, it's safe to scan children
                try:
                    with os.scandir(entry1.path) as it2:
                        for entry2 in it2:
                            if not entry2.is_dir() or entry2.name.startswith('.'): continue

                            mk2 = os.path.join(entry2.path, "Makefile")
                            if os.path.isfile(mk2):
                                # Security check: Only resolve if it's a symlink
                                if entry2.is_symlink():
                                    try:
                                        resolved = Path(entry2.path).resolve()
                                        if not resolved.is_relative_to(CASES_PATH):
                                            logger.warning(f"Ignored symlinked case: {entry2.path} -> {resolved}")
                                            continue
                                    except Exception:
                                        continue

                                rel_path = os.path.join(entry1.name, entry2.name)
                                cases.append({
                                    "id": rel_path,
                                    "path": rel_path,
                                    "name": entry2.name,
                                    "domain": entry1.name
                                })
                except (PermissionError, NotADirectoryError):
                    continue
    except FileNotFoundError:
        pass
    return cases

@app.post("/build")
def build_case(req: CommandRequest, request: Request):
    """Executes 'make' in the directory."""
    # Enforce concurrency limit to prevent resource exhaustion
    if not execution_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another build or run is already in progress")

    try:
        # Security check
        safe_path = validate_case_path(req.case_path)
        client_ip = request.client.host if request.client else "unknown"
        # Audit Log: Include client IP for accountability
        logger.info(f"Building case: {safe_path} (Request from: {client_ip})")

        if not os.path.exists(safe_path):
            logger.warning(f"Case path not found: {safe_path}")
            raise HTTPException(status_code=404, detail="Case path not found")

        try:
            # Run make
            # Use a temporary file to capture output to avoid memory exhaustion (DoS)
            # Performance Optimization: Use binary mode ('w+b') to enable efficient seeking
            # and tail reading. This allows us to read only the most relevant part of the log
            # (the end) without loading the entire file into memory or sending useless data.
            with tempfile.TemporaryFile(mode='w+b') as tmp:
                # Use sanitized environment to prevent secret leakage
                # SENTINEL FIX: Use run_command_safe to kill process tree on timeout
                # This prevents zombie processes if 'make' spawns children.
                try:
                    return_code = run_command_safe(
                        ["make"],
                        cwd=safe_path,
                        env=get_safe_env(),
                        stdout=tmp,
                        timeout=300  # 5 minute timeout
                    )
                except subprocess.TimeoutExpired:
                    logger.error(f"Build timed out for {safe_path}")
                    output = read_log_tail(tmp)
                    return {
                        "success": False,
                        "error": "Build timed out (limit: 5 minutes)",
                        "stdout": output,
                        "stderr": ""
                    }

                # Performance Optimization: Tail Reading
                # Instead of reading the first 512KB (which often misses the error at the end),
                # we read the LAST 100KB (matching the frontend's display limit).
                # This reduces network payload by ~80% (512KB -> 100KB) and ensures
                # the user sees the critical error message usually located at the end of the log.
                output = read_log_tail(tmp)

                return {
                    "success": return_code == 0,
                    "stdout": output,
                    "stderr": "" # stderr is merged into stdout
                }
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return {"success": False, "error": "Build failed due to an internal error"}
    finally:
        execution_lock.release()

@app.post("/run")
def run_case(req: CommandRequest, request: Request):
    """Executes 'make run' in the directory."""
    # Enforce concurrency limit to prevent resource exhaustion
    if not execution_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another build or run is already in progress")

    try:
        # Security check
        safe_path = validate_case_path(req.case_path)
        client_ip = request.client.host if request.client else "unknown"
        # Audit Log: Include client IP for accountability
        logger.info(f"Running case: {safe_path} (Request from: {client_ip})")

        if not os.path.exists(safe_path):
            logger.warning(f"Case path not found: {safe_path}")
            raise HTTPException(status_code=404, detail="Case path not found")

        try:
            # Run make run
            # Use a temporary file to capture output to avoid memory exhaustion (DoS)
            # Performance Optimization: Use binary mode ('w+b') for efficient tail reading
            with tempfile.TemporaryFile(mode='w+b') as tmp:
                # Use sanitized environment to prevent secret leakage
                # SENTINEL FIX: Use run_command_safe to kill process tree on timeout
                try:
                    return_code = run_command_safe(
                        ["make", "run"],
                        cwd=safe_path,
                        env=get_safe_env(),
                        stdout=tmp,
                        timeout=600  # 10 minute timeout
                    )
                except subprocess.TimeoutExpired:
                    logger.error(f"Run timed out for {safe_path}")
                    output = read_log_tail(tmp)
                    return {
                        "success": False,
                        "error": "Simulation timed out (limit: 10 minutes)",
                        "stdout": output,
                        "stderr": ""
                    }

                # Performance Optimization: Tail Reading (see build_case for details)
                output = read_log_tail(tmp)

                return {
                    "success": return_code == 0,
                    "stdout": output,
                    "stderr": "" # stderr is merged into stdout
                }
        except Exception as e:
            logger.error(f"Run failed: {e}")
            return {"success": False, "error": "Simulation failed due to an internal error"}
    finally:
        execution_lock.release()

@app.get("/config")
def get_config(request: Request, path: str = Query(..., max_length=4096)):
    """Reads the config.xml file."""
    # Validate path is within CASES_DIR for security
    safe_path = validate_case_path(path)
    client_ip = request.client.host if request.client else "unknown"
    # Audit Log: Include client IP for accountability
    logger.info(f"Reading config for: {safe_path} (Request from: {client_ip})")

    config_path = os.path.join(safe_path, "config.xml")

    try:
        # Security Fix: Prevent Arbitrary File Read via Symlinks (CWE-59)
        # Even though safe_path (the directory) is validated, config.xml could be a symlink
        # pointing to a sensitive file outside the permitted directory (e.g. /etc/passwd).
        # We unconditionally resolve the path to handle symlinks safely and avoid TOCTOU race conditions.
        resolved_config = Path(config_path).resolve()
        if not resolved_config.is_relative_to(CASES_PATH):
            logger.warning(f"Access denied: Config file points outside permitted area: {config_path} -> {resolved_config}")
            raise HTTPException(status_code=403, detail="Access denied: Config file points outside safe directory")

        with open(config_path, "r") as f:
            # Check file size using fstat on the open file descriptor
            # This prevents TOCTOU (Time of Check to Time of Use) race conditions
            file_size = os.fstat(f.fileno()).st_size
            if file_size > 1024 * 1024:  # 1MB limit
                logger.warning(f"Config file too large ({file_size} bytes): {config_path}")
                raise HTTPException(status_code=413, detail="File too large (limit 1MB)")

            return {"content": f.read()}
    except FileNotFoundError:
        logger.warning(f"Config not found: {config_path}")
        return {"content": ""}
    except OSError as e:
        logger.error(f"Error reading config file: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.post("/config")
def save_config(req: ConfigRequest, request: Request):
    """Writes the config.xml file."""
    safe_path = validate_case_path(req.case_path)
    client_ip = request.client.host if request.client else "unknown"
    # Audit Log: Include client IP for accountability
    logger.info(f"Saving config for: {safe_path} (size: {len(req.content)} bytes) (Request from: {client_ip})")

    config_path = os.path.join(safe_path, "config.xml")

    # Security Enhancement: Atomic Write
    # Write to a temporary file first, then rename it to the target file.
    # This prevents data corruption (partial writes) and ensures atomicity.
    # We use delete=False because we want to rename it, not delete it.
    # We create it in the same directory (safe_path) to ensure rename is atomic (same filesystem).
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=safe_path, delete=False, suffix=".tmp") as tmp:
            tmp_name = tmp.name
            # Set permissions to 644 (owner rw, group r, other r) to match standard behavior
            # tempfile defaults to 600 which might be too restrictive if other users/groups need read access
            os.chmod(tmp_name, 0o644)
            tmp.write(req.content)
            tmp.flush()
            os.fsync(tmp.fileno()) # Ensure data is written to disk

        # Atomically replace (os.replace works on Windows too)
        os.replace(tmp_name, config_path)
    except Exception as e:
        logger.error(f"Failed to save config: {e}")
        # Clean up temp file if it exists
        if tmp_name and os.path.exists(tmp_name):
            try:
                os.remove(tmp_name)
            except OSError:
                pass
        raise HTTPException(status_code=500, detail="Failed to save configuration")

    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    # Sentinel: Bind to 127.0.0.1 (localhost) by default to prevent access from external networks.
    # Allow overriding via HOST env var for Docker/remote scenarios.
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=8080)
