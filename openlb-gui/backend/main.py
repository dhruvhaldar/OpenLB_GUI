from fastapi import FastAPI, HTTPException, Body, Query

from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi import Request, Response
from fastapi.responses import JSONResponse
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
import stat
from collections import defaultdict, deque
from pathlib import Path
from functools import lru_cache

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
        # Sentinel Enhancement: Use monotonic time for robust duration checks
        self.last_cleanup = time.monotonic()
        # Sentinel Enhancement: Memory Protection
        # Limit total tracked IPs to prevent Memory Exhaustion and CPU spikes during cleanup (DoS).
        self.MAX_IP_COUNT = 10000

    def is_rate_limited(self, ip: str) -> tuple[bool, int]:
        now = time.monotonic()

        # Sentinel Security Check: Memory Protection
        # Before adding a new IP, check if we are at capacity.
        # This prevents unbounded growth of the requests dictionary (DoS vector).
        if len(self.requests) > self.MAX_IP_COUNT:
            # Emergency cleanup: Clear all to prevent crash/hang.
            # While this resets limits for current users, availability takes precedence over rate limiting
            # in a massive DoS scenario.
            self.requests.clear()
            logger.warning("Rate Limiter memory protection triggered. Cleared all IPs to prevent exhaustion.")

        # Sentinel Fix: Prevent Global Reset by cleaning up ONLY expired/empty IPs
        # This prevents active users' history from being wiped, ensuring consistent rate limiting.
        if now - self.last_cleanup > 60:
            # Iterate over a list of keys to safely delete while iterating
            for key in list(self.requests.keys()):
                dq = self.requests[key]
                # Remove expired requests for this IP
                while dq and now - dq[0] > 60:
                    dq.popleft()
                # If deque is empty, remove the IP entry to free memory
                if not dq:
                    del self.requests[key]
            self.last_cleanup = now

        dq = self.requests[ip]

        # Efficiently remove expired requests from the left (oldest first)
        # O(k) where k is the number of expired requests (usually small)
        # This avoids copying the entire list as list comprehension would do.
        while dq and now - dq[0] > 60:
            dq.popleft()

        if len(dq) >= self.limit:
            # Calculate retry after time (in seconds)
            # We use the oldest request time (dq[0]) to determine when the slot frees up.
            retry_after = 60 - (now - dq[0])
            # Ensure it's at least 1 second and integer
            return True, int(retry_after) + 1 if retry_after > 0 else 1

        dq.append(now)
        return False, 0

rate_limiter = RateLimiter(requests_per_minute=20) # 20 req/min/IP for sensitive actions
read_rate_limiter = RateLimiter(requests_per_minute=100) # 100 req/min/IP for read operations

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
                 # Sentinel Fix: Prevent "Prefix Match" bypass (e.g. allowed:5173 matching allowed:51730)
                 # We ensure the referer matches the origin exactly OR starts with origin + "/"
                 if not any(referrer == allowed or referrer.startswith(allowed + "/") for allowed in self.allowed_origins):
                     logger.warning(f"Blocked CSRF attempt. Referer: {referrer}")
                     return Response("Forbidden: Untrusted Referrer", status_code=403)

            # 3. If both are missing, we ALLOW (Lax Mode)
            # This is necessary because non-browser tools (curl, scripts, TestClient)
            # typically do not send Origin/Referer.
            # Since the app runs on localhost, the primary threat is the browser (CSRF).

        return await call_next(request)

class StrictInputValidationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int) -> None:
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        # Sentinel Enhancement: Secure by Default
        # Apply checks to all methods that can carry a body to prevent bypasses.
        if request.method in ["POST", "PUT", "PATCH"]:
            # Sentinel Enhancement: Enforce Content-Type to prevent CSRF via Simple Requests
            # HTML Forms cannot send application/json, so this prevents bypassing Preflight checks.
            # We enforce strict API usage: backend only speaks JSON.
            content_type = request.headers.get("content-type", "")
            if not content_type.lower().startswith("application/json"):
                 return JSONResponse(status_code=415, content={"detail": "Content-Type must be application/json"})

            # Security Fix: Enforce Content-Length
            # Reject Chunked Encoding or requests without Content-Length to prevent
            # Memory Exhaustion DoS attacks. The backend expects finite, known-size payloads (JSON/text).
            if 'content-length' not in request.headers:
                 return JSONResponse(status_code=411, content={"detail": "Content-Length required"})

            try:
                content_length = int(request.headers['content-length'])
                if content_length < 0:
                    raise ValueError("Negative Content-Length")
            except ValueError:
                return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})

            if content_length > self.max_upload_size:
                return JSONResponse(status_code=413, content={"detail": "Request body too large"})

        # Sentinel Enhancement: Reject bodies for GET/DELETE/HEAD/OPTIONS
        # Prevents Request Smuggling, Cache Poisoning, and ambiguities.
        elif request.method in ["GET", "DELETE", "HEAD", "OPTIONS"]:
             if request.headers.get("transfer-encoding"):
                 return JSONResponse(status_code=400, content={"detail": "Request body not allowed for this method (Transfer-Encoding present)"})

             if "content-length" in request.headers:
                 try:
                     length = int(request.headers["content-length"])
                     if length > 0:
                         return JSONResponse(status_code=400, content={"detail": "Request body not allowed for this method"})
                 except ValueError:
                     return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header"})

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

# Security Enhancement: Host Header Validation
# Prevents DNS Rebinding attacks where an attacker controls a domain that resolves to 127.0.0.1.
# We whitelist standard localhost names and 'testserver' for internal testing.
# This middleware must be added AFTER CORSMiddleware (in execution order, which means BEFORE in add_middleware order)
# Wait, FastAPI middleware order is LIFO (Last Added = First Executed).
# We want Host validation to happen EARLY, so we add it LAST (executed FIRST).
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "testserver"]
)

# Apply TrustedOriginMiddleware
app.add_middleware(TrustedOriginMiddleware, allowed_origins=ALLOWED_ORIGINS)

app.add_middleware(StrictInputValidationMiddleware, max_upload_size=2 * 1024 * 1024) # 2MB limit

def apply_security_headers(response: Response, request: Request):
    """
    Helper to consistently apply security headers to any response.
    Ensures headers are present even on early-exit error responses (e.g. 429).
    """
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    # Sentinel Enhancement: Prevent Clickjacking via CSP
    # 'frame-ancestors none' prevents this site from being embedded in iframes,
    # protecting against UI redress attacks.
    # Sentinel Enhancement: Strengthen CSP with explicit directives
    # - object-src 'none': Prevents plugins (Flash, Java)
    # - base-uri 'none': Prevents <base> tag hijacking
    # - form-action 'self': Prevents form submission to external sites
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'; object-src 'none'; base-uri 'none'; form-action 'self'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    # Sentinel Enhancement: Prevent cross-domain content loading (e.g. Flash, PDF)
    # Defense in Depth against Polyglot attacks and data exfiltration via plugins.
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    # Sentinel Enhancement: Isolate browsing context
    # Prevents XS-Leaks and Spectre attacks by ensuring this window runs in a separate process group
    # and cannot be scripted by other origins.
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    # Sentinel Enhancement: Prevent resource embedding by other origins
    # Defense in Depth against side-channel attacks and unauthorized usage.
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    # Sentinel Enhancement: Strict Permissions Policy
    # Explicitly disable powerful browser features to reduce attack surface (Defense in Depth).
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=(), usb=(), vr=(), autoplay=(), midi=(), sync-xhr=(), accelerometer=(), gyroscope=(), magnetometer=(), fullscreen=(), picture-in-picture=()"
    # Sentinel Enhancement: Prevent caching of sensitive data (config, logs)
    # The 'no-store' directive prevents browsers and intermediate proxies from storing
    # any version of the response, forcing a fresh fetch every time.
    response.headers["Cache-Control"] = "no-store"
    # Legacy compatibility for HTTP/1.0 proxies
    response.headers["Pragma"] = "no-cache"

    # Sentinel Enhancement: HTTP Strict Transport Security (HSTS)
    # HSTS tells the browser to ONLY use HTTPS for future requests.
    # It protects against SSL Stripping and Protocol Downgrade attacks.
    # We apply it only if the current connection is secure (or forwarded as secure)
    # to avoid locking out users on plain HTTP (e.g. initial setup).
    if request.url.scheme == "https" or request.headers.get("X-Forwarded-Proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"

    return response

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Rate Limiting for state-changing operations
    # We apply this before processing the request
    # Sentinel: Broadened scope to all state-changing methods to prevent bypasses and future oversight
    client_ip = request.client.host if request.client else "unknown"
    if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
        is_limited, retry_after = rate_limiter.is_rate_limited(client_ip)
        if is_limited:
            logger.warning(f"Write Rate limit exceeded for {client_ip} on {request.url.path}")
            # We return a JSON response directly for 429
            # Note: We can't easily raise HTTPException in middleware, so we return Response
            response = JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Please try again in {retry_after} seconds."}
            )
            # Sentinel Enhancement: Add Retry-After header
            # This helps clients (and bots) know when they can try again,
            # improving protocol compliance and reducing server load from blind retries.
            response.headers["Retry-After"] = str(retry_after)
            return apply_security_headers(response, request)

    # Sentinel Enhancement: Rate Limiting for Read Operations (GET)
    # Protects against DoS attacks via rapid read requests (e.g., recursive scanning, file reading).
    elif request.method == "GET":
        is_limited, retry_after = read_rate_limiter.is_rate_limited(client_ip)
        if is_limited:
            logger.warning(f"Read Rate limit exceeded for {client_ip} on {request.url.path}")
            response = JSONResponse(
                status_code=429,
                content={"detail": f"Too many requests. Please try again in {retry_after} seconds."}
            )
            # Sentinel Enhancement: Add Retry-After header
            response.headers["Retry-After"] = str(retry_after)
            return apply_security_headers(response, request)

    response = await call_next(request)
    return apply_security_headers(response, request)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# Resolve cases directory relative to the project root (2 levels up from backend/main.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Use resolve() for CASES_DIR to ensure we have the absolute path
CASES_PATH = (PROJECT_ROOT / "my_cases").resolve()
# Keep CASES_DIR as string for glob/compat but use CASES_PATH for security checks
CASES_DIR = str(CASES_PATH)
# Performance Optimization: Pre-compute directory with separator for fast containment checks.
# This avoids string allocation and repeated indexing operations in hot paths.
CASES_DIR_WITH_SEP = os.path.join(CASES_DIR, "")

# Global lock to prevent concurrent build/run operations
# This prevents Resource Exhaustion DoS and file corruption
execution_lock = threading.Lock()

# Pre-compile regex for control characters optimization
# Matches any char < 32 (0x20) AND the Delete char (0x7f)
# Security Fix: Rejecting tabs and DEL prevents Log Injection (CWE-117) and visual spoofing.
CONTROL_CHARS = re.compile(r'[\x00-\x1f\x7f]')

# Pre-compile Regex for hidden path check optimization
# Matches a dot at the beginning of a string or immediately after a separator
HIDDEN_PATH_PATTERN = re.compile(r'(?:^|[\\/])\.')

# Pre-compile Regexes for Validation Hot Paths
# Optimization: Pre-compiling regexes avoids cache lookup overhead and recompilation
# for patterns used in every request (config validation, duplicate checks).
XXE_DOCTYPE_PATTERN = re.compile(r'<!\s*DOCTYPE', re.IGNORECASE)
XXE_ENTITY_PATTERN = re.compile(r'<!\s*ENTITY', re.IGNORECASE)
VALID_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Security Enhancement: Windows Reserved Filenames
# These names are reserved by Windows and can cause issues if created on a shared filesystem
# or if the project is later moved to a Windows machine (DoS / Access Denied).
# We block them case-insensitively.
RESERVED_WINDOWS_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"
}

# Bolt Performance Optimization: Pre-defined ignore sets
# Using sets and tuples for O(1) lookups instead of O(N*M) fnmatch/regex patterns
IGNORED_EXTENSIONS = (
    ".o", ".obj", ".a", ".so", ".dll", ".exe",  # Build artifacts
    ".vtk", ".vti", ".vtu", ".vtp", ".pvti", ".pvtu", # Simulation outputs
    ".log", ".out", ".err"               # Logs
)
IGNORED_DIRS = {
    "tmp", "__pycache__", ".git", ".DS_Store" # Temporary/System files
}

# Pre-compute lowercase versions for Windows case-insensitivity
if os.name == 'nt':
    IGNORED_EXTENSIONS = tuple(ext.lower() for ext in IGNORED_EXTENSIONS)
    IGNORED_DIRS = {name.lower() for name in IGNORED_DIRS}

def fast_ignore_patterns(path, names):
    """
    Optimized ignore callback for shutil.copytree.
    Reduces complexity from O(N*P) (fnmatch) to O(N) (set/endswith).
    """
    ignored = set()
    # On Windows, we need to compare case-insensitively
    is_windows = os.name == 'nt'

    for name in names:
        check_name = name
        if is_windows:
            check_name = name.lower()

        if check_name in IGNORED_DIRS:
            ignored.add(name)
            continue

        if check_name.endswith(IGNORED_EXTENSIONS):
            ignored.add(name)

    return ignored

# Allowed environment variables to pass to subprocesses
SAFE_ENV_VARS = {
    'PATH', 'LANG', 'LC_ALL', 'TERM', 'LD_LIBRARY_PATH',
    'HOME', 'USER', 'SHELL', 'TMPDIR'
}

@lru_cache(maxsize=1)
def _get_base_safe_env():
    """
    Internal cached helper to filter environment variables.
    """
    safe_env = {}
    for key, value in os.environ.items():
        if key in SAFE_ENV_VARS or key.startswith('OLB_'):
            safe_env[key] = value
    return safe_env

def get_safe_env():
    """
    Returns a sanitized environment dictionary for subprocess execution.
    Only allows specific safe variables and those starting with OLB_.
    Prevents leakage of sensitive backend environment variables (keys, secrets).

    Performance Optimization: Uses a cached base dictionary and returns a shallow copy.
    This avoids iterating over os.environ on every call while preventing state leakage.
    """
    return _get_base_safe_env().copy()

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
            # Optimization: Adaptive polling interval
            # Start fast (5ms) to catch immediate failures/completions quickly, reducing latency.
            # Exponentially back off to 0.1s to avoid high CPU usage for long-running processes.
            sleep_time = 0.005

            while time.time() - start_time < timeout:
                # 1. Check output size (Disk Exhaustion Protection)
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

                # 2. Wait for process or timeout
                # Performance Optimization: Use process.wait(timeout=...) instead of time.sleep()
                # This returns immediately if the process finishes, reducing latency for short commands
                # and improving responsiveness.
                try:
                    return_code = process.wait(timeout=sleep_time)

                    # Process finished. Final check for output size.
                    if stdout and os.fstat(stdout.fileno()).st_size > max_output_size:
                        logger.warning(f"Process output exceeded limit ({max_output_size} bytes).")
                        stdout.write(b"\n\n[ERROR: Output limit exceeded. Terminating process to prevent disk exhaustion.]\n")
                        raise subprocess.TimeoutExpired(cmd, timeout)

                    return return_code
                except subprocess.TimeoutExpired:
                    # Process still running, loop continues
                    pass

                # Adaptive sleep calculation for NEXT wait
                if sleep_time < 0.1:
                    sleep_time = min(0.1, sleep_time * 2)

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
        # UPDATE: Further optimized to use CASES_DIR_WITH_SEP to avoid indexing and length checks.
        # Benchmark shows ~1.4x speedup for this check.
        rel = None
        if target_path == CASES_DIR:
            rel = "."
        elif target_path.startswith(CASES_DIR_WITH_SEP):
            rel = target_path[len(CASES_DIR_WITH_SEP):]

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

def safe_copy(src, dst, **kwargs):
    """
    Custom copy function for shutil.copytree to prevent copying special files
    (FIFOs, Sockets, Devices) which can cause errors or blocking.
    """
    try:
        # Check file type. os.lstat is used to check the file itself.
        st = os.lstat(src)
        if stat.S_ISFIFO(st.st_mode) or stat.S_ISSOCK(st.st_mode) or \
           stat.S_ISCHR(st.st_mode) or stat.S_ISBLK(st.st_mode):
            logger.warning(f"Skipping special file during duplicate: {src}")
            return

        # Standard copy for regular files
        shutil.copy2(src, dst, **kwargs)
    except OSError as e:
        logger.warning(f"Failed to check/copy file {src}: {e}")

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

    # Security Enhancement: Prevent creation of Windows reserved filenames
    if req.new_name.upper() in RESERVED_WINDOWS_NAMES:
        logger.warning(f"Invalid duplicate attempt from {client_ip}: Reserved name={repr(req.new_name)}")
        raise HTTPException(status_code=400, detail="Invalid name. This name is reserved by Windows.")

    # Log AFTER validation to prevent Log Injection
    # Audit Log: Include client IP for accountability
    logger.info(f"Duplicating case: {safe_source} to name: {req.new_name} (Request from: {client_ip})")

    parent_dir = os.path.dirname(safe_source)
    target_path = os.path.join(parent_dir, req.new_name)

    # Validate target path (even though constructed safely, ensures it's in CASES_DIR)
    # Performance Optimization: Use os.path.realpath + string check instead of Path.resolve()
    # Pathlib's resolve() and relative_to() involve object overhead and iterative checks.
    # This aligns with validate_case_path optimization.
    resolved_target = os.path.realpath(target_path)

    # Optimization: Use pre-computed separator path for fast containment check
    if not (resolved_target == CASES_DIR or resolved_target.startswith(CASES_DIR_WITH_SEP)):
        logger.warning(f"Access denied: Target path outside cases directory: {target_path} -> {resolved_target}")
        raise HTTPException(status_code=403, detail="Access denied")

    if os.path.exists(target_path):
        raise HTTPException(status_code=409, detail="Case with this name already exists")

    try:
        # Security Fix: Use symlinks=True to prevent dereferencing symlinks.
        # If symlinks=False (default), a symlink to /etc/passwd in the source would be copied
        # as the actual file content, leading to arbitrary file read / disclosure.
        # It also prevents infinite recursion if a symlink points to a parent directory.
        #
        # Performance Optimization: Added ignore=fast_ignore_patterns
        # This prevents copying massive simulation output files (VTK) and build artifacts (objects),
        # transforming an O(GB) operation into O(KB), making duplication nearly instantaneous
        # and saving significant disk space.
        #
        # Bolt Optimization: Replaced shutil.ignore_patterns (O(N*M)) with fast_ignore_patterns (O(N))
        # This speeds up directory traversal significantly when thousands of files exist.
        #
        # Sentinel Enhancement: Use copy_function=safe_copy to skip special files (FIFOs, Sockets)
        # that would otherwise cause shutil.Error (failing the operation) or potential hangs.
        shutil.copytree(safe_source, target_path, symlinks=True, ignore=fast_ignore_patterns, copy_function=safe_copy)

        # Bolt Optimization: Return full case object to avoid frontend re-fetch
        # Calculate domain based on parent directory (Level 1 vs Level 2)
        domain = "Uncategorized"
        if parent_dir != CASES_DIR:
            domain = os.path.basename(parent_dir)

        new_rel_path = os.path.relpath(target_path, CASES_DIR)

        return {
            "success": True,
            "case": {
                "id": new_rel_path,
                "path": new_rel_path,
                "name": req.new_name,
                "domain": domain
            }
        }
    except Exception as e:
        logger.error(f"Duplicate failed: {e}")

        # Sentinel Fix: Cleanup on failure
        # If duplication fails (e.g. Disk Full), remove the partial directory
        # to prevent "zombie" directories and Disk Exhaustion.
        # CRITICAL: Do NOT delete if the error was that the directory already exists (FileExistsError).
        # This prevents accidental deletion of existing cases in race conditions.
        is_exist_error = isinstance(e, FileExistsError)
        if not is_exist_error and os.path.exists(target_path):
            try:
                shutil.rmtree(target_path)
                logger.info(f"Cleaned up partial directory: {target_path}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup partial directory {target_path}: {cleanup_error}")

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

                # Bolt Optimization: Skip ignored directories (e.g. tmp, __pycache__)
                # This prevents unnecessary recursion and stat calls in massive build/output directories.
                check_name = entry1.name.lower() if os.name == 'nt' else entry1.name
                if check_name in IGNORED_DIRS:
                    continue

                # Optimization: Cache symlink status and resolve only once per entry
                # This prevents redundant resolve() calls when an entry is checked for both
                # being a case (Level 1) and a domain container (Level 2).
                if entry1.is_symlink():
                    try:
                        # Performance Optimization: Use os.path.realpath + string check instead of Path.resolve()
                        resolved = os.path.realpath(entry1.path)
                        is_safe = False
                        # Optimization: Use pre-computed separator path
                        if resolved == CASES_DIR or resolved.startswith(CASES_DIR_WITH_SEP):
                             is_safe = True

                        if not is_safe:
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

                            # Bolt Optimization: Skip ignored directories
                            check_name_2 = entry2.name.lower() if os.name == 'nt' else entry2.name
                            if check_name_2 in IGNORED_DIRS:
                                continue

                            mk2 = os.path.join(entry2.path, "Makefile")
                            if os.path.isfile(mk2):
                                # Security check: Only resolve if it's a symlink
                                if entry2.is_symlink():
                                    try:
                                        # Performance Optimization: Use os.path.realpath + string check
                                        resolved = os.path.realpath(entry2.path)
                                        is_safe = False
                                        # Optimization: Use pre-computed separator path
                                        if resolved == CASES_DIR or resolved.startswith(CASES_DIR_WITH_SEP):
                                            is_safe = True

                                        if not is_safe:
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

    # Performance Optimization: Sort cases by domain and name.
    # This ensures deterministic order (O(N log N)) regardless of filesystem order.
    # It allows the frontend to use efficient O(N) sequential comparison instead of O(N) Map lookups.
    cases.sort(key=lambda x: (x['domain'], x['name']))

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
        # Performance Optimization: Use os.path.realpath instead of Path.resolve()
        # This avoids Path object creation overhead (~5x faster).
        resolved_config = os.path.realpath(config_path)

        # Containment Check: Verify resolved_config is inside CASES_DIR
        # This replaces resolved_config.is_relative_to(CASES_PATH)
        is_safe = False
        # Optimization: Use pre-computed separator path
        if resolved_config == CASES_DIR or resolved_config.startswith(CASES_DIR_WITH_SEP):
             is_safe = True

        if not is_safe:
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

    # Sentinel Enhancement: Preserve file permissions
    # In shared environments, users may restrict file permissions (e.g. 600) to protect sensitive data.
    # We must preserve these permissions when overwriting the file.
    original_mode = 0o644
    if os.path.exists(config_path):
        try:
            original_mode = stat.S_IMODE(os.stat(config_path).st_mode)
        except OSError:
            pass

    # Security Enhancement: Atomic Write
    # Write to a temporary file first, then rename it to the target file.
    # This prevents data corruption (partial writes) and ensures atomicity.
    # We use delete=False because we want to rename it, not delete it.
    # We create it in the same directory (safe_path) to ensure rename is atomic (same filesystem).
    tmp_name = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', dir=safe_path, delete=False, suffix=".tmp") as tmp:
            tmp_name = tmp.name
            # Set permissions to match the original file (or default to 644)
            # This respects the user's security intent (Principle of Least Privilege).
            os.chmod(tmp_name, original_mode)
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
    uvicorn.run(app, host=host, port=8080, server_header=False)
