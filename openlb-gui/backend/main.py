from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi import Request
from pydantic import BaseModel, field_validator, Field
import os
import subprocess
import logging
import tempfile
import re
import threading
import shutil
import time
from collections import defaultdict
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
        self.requests = defaultdict(list)
        # Clean up old entries periodically (in a real app, use Redis)
        self.last_cleanup = time.time()

    def is_rate_limited(self, ip: str) -> bool:
        now = time.time()
        # Simple cleanup every minute
        if now - self.last_cleanup > 60:
            self.requests.clear()
            self.last_cleanup = now

        # Filter out requests older than 1 minute
        self.requests[ip] = [t for t in self.requests[ip] if now - t < 60]

        if len(self.requests[ip]) >= self.limit:
            return True

        self.requests[ip].append(now)
        return False

rate_limiter = RateLimiter(requests_per_minute=20) # 20 req/min/IP for sensitive actions

# Allow CORS for frontend dev
# Restrict to standard local dev ports to prevent access from arbitrary sites
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    # Rate Limiting for state-changing operations
    # We apply this before processing the request
    if request.method in ["POST", "DELETE"] and request.url.path in ["/build", "/run", "/cases/duplicate", "/cases"]:
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
# Matches any char < 32 (0x20) EXCEPT tab (0x09)
# \x00-\x08 matches 0-8
# \x0a-\x1f matches 10-31
CONTROL_CHARS = re.compile(r'[\x00-\x08\x0a-\x1f]')

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

        # Resolve the input path to handle '..' and symlinks
        target_path = Path(path_str).resolve()

        # Check if the path is relative to CASES_PATH
        if not target_path.is_relative_to(CASES_PATH):
             # Use repr() to prevent log injection
             logger.warning(f"Access denied for path: {repr(path_str)}")
             raise HTTPException(status_code=403, detail="Access denied")

        # Security check: Prevent operations on the root cases directory itself
        if target_path == CASES_PATH:
             logger.warning(f"Attempted operation on root cases directory: {repr(path_str)}")
             raise HTTPException(status_code=403, detail="Access denied: Cannot operate on root cases directory")

        return str(target_path)
    except (ValueError, RuntimeError):
        # Handle cases where is_relative_to might fail or other path errors
        # Use repr() to prevent log injection
        logger.error(f"Error validating path: {repr(path_str)}")
        raise HTTPException(status_code=403, detail="Access denied")

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
        if re.search(r'<!\s*DOCTYPE', v, re.IGNORECASE) or re.search(r'<!\s*ENTITY', v, re.IGNORECASE):
            raise ValueError('XML Document Type Definitions (DTD) are not allowed for security reasons')

        return v

@app.post("/cases/duplicate")
def duplicate_case(req: DuplicateRequest):
    """Duplicates an existing case."""
    safe_source = validate_case_path(req.source_path)
    logger.info(f"Duplicating case: {safe_source} to name: {req.new_name}")

    if not re.match(r'^[a-zA-Z0-9_-]+$', req.new_name):
        raise HTTPException(status_code=400, detail="Invalid name. Use alphanumeric, underscore, and hyphen only.")

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
        shutil.copytree(safe_source, target_path)
        return {"success": True, "new_path": target_path}
    except Exception as e:
        logger.error(f"Duplicate failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to duplicate case")

@app.delete("/cases")
def delete_case(case_path: str):
    """Deletes a case directory."""
    safe_path = validate_case_path(case_path)
    logger.info(f"Deleting case: {safe_path}")

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
                        "path": entry1.path,
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
                                    "path": entry2.path,
                                    "name": entry2.name,
                                    "domain": entry1.name
                                })
                except (PermissionError, NotADirectoryError):
                    continue
    except FileNotFoundError:
        pass
    return cases

@app.post("/build")
def build_case(req: CommandRequest):
    """Executes 'make' in the directory."""
    # Enforce concurrency limit to prevent resource exhaustion
    if not execution_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another build or run is already in progress")

    try:
        # Security check
        safe_path = validate_case_path(req.case_path)
        logger.info(f"Building case: {safe_path}")

        if not os.path.exists(safe_path):
            logger.warning(f"Case path not found: {safe_path}")
            raise HTTPException(status_code=404, detail="Case path not found")

        try:
            # Run make
            # Use a temporary file to capture output to avoid memory exhaustion (DoS)
            with tempfile.TemporaryFile(mode='w+') as tmp:
                # Use sanitized environment to prevent secret leakage
                result = subprocess.run(
                    ["make"],
                    cwd=safe_path,
                    env=get_safe_env(),
                    stdout=tmp,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                    timeout=300  # 5 minute timeout
                )

                # Read back only a safe amount of output
                tmp.seek(0)
                output = tmp.read(512 * 1024) # 512KB limit
                if tmp.read(1):
                    output += "\n[Output truncated due to size limit]"

                return {
                    "success": result.returncode == 0,
                    "stdout": output,
                    "stderr": "" # stderr is merged into stdout
                }
        except subprocess.TimeoutExpired:
            logger.error(f"Build timed out for {safe_path}")
            return {"success": False, "error": "Build timed out (limit: 5 minutes)"}
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return {"success": False, "error": "Build failed due to an internal error"}
    finally:
        execution_lock.release()

@app.post("/run")
def run_case(req: CommandRequest):
    """Executes 'make run' in the directory."""
    # Enforce concurrency limit to prevent resource exhaustion
    if not execution_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="Another build or run is already in progress")

    try:
        # Security check
        safe_path = validate_case_path(req.case_path)
        logger.info(f"Running case: {safe_path}")

        if not os.path.exists(safe_path):
            logger.warning(f"Case path not found: {safe_path}")
            raise HTTPException(status_code=404, detail="Case path not found")

        try:
            # Run make run
            # Use a temporary file to capture output to avoid memory exhaustion (DoS)
            with tempfile.TemporaryFile(mode='w+') as tmp:
                # Use sanitized environment to prevent secret leakage
                result = subprocess.run(
                    ["make", "run"],
                    cwd=safe_path,
                    env=get_safe_env(),
                    stdout=tmp,
                    stderr=subprocess.STDOUT,
                    text=True,
                    check=False,
                    timeout=600  # 10 minute timeout
                )

                # Read back only a safe amount of output
                tmp.seek(0)
                output = tmp.read(512 * 1024) # 512KB limit
                if tmp.read(1):
                    output += "\n[Output truncated due to size limit]"

                return {
                    "success": result.returncode == 0,
                    "stdout": output,
                    "stderr": "" # stderr is merged into stdout
                }
        except subprocess.TimeoutExpired:
            logger.error(f"Run timed out for {safe_path}")
            return {"success": False, "error": "Simulation timed out (limit: 10 minutes)"}
        except Exception as e:
            logger.error(f"Run failed: {e}")
            return {"success": False, "error": "Simulation failed due to an internal error"}
    finally:
        execution_lock.release()

@app.get("/config")
def get_config(path: str):
    """Reads the config.xml file."""
    # Validate path is within CASES_DIR for security
    safe_path = validate_case_path(path)
    logger.info(f"Reading config for: {safe_path}")

    config_path = os.path.join(safe_path, "config.xml")

    try:
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
def save_config(req: ConfigRequest):
    """Writes the config.xml file."""
    safe_path = validate_case_path(req.case_path)
    logger.info(f"Saving config for: {safe_path} (size: {len(req.content)} bytes)")

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
