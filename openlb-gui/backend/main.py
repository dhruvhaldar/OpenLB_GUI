from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel, field_validator
import os
import subprocess
import glob
import logging
import tempfile
import re
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("openlb-backend")

app = FastAPI()

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
async def add_security_headers(request, call_next):
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

def validate_case_path(path_str: str) -> str:
    """
    Validates that the path is within the CASES_DIR.
    Returns the absolute path as a string if valid.
    Raises HTTPException if invalid.
    """
    try:
        # Resolve the input path to handle '..' and symlinks
        target_path = Path(path_str).resolve()

        # Check if the path is relative to CASES_PATH
        if not target_path.is_relative_to(CASES_PATH):
             # Use repr() to prevent log injection
             logger.warning(f"Access denied for path: {repr(path_str)}")
             raise HTTPException(status_code=403, detail="Access denied")

        return str(target_path)
    except (ValueError, RuntimeError):
        # Handle cases where is_relative_to might fail or other path errors
        # Use repr() to prevent log injection
        logger.error(f"Error validating path: {repr(path_str)}")
        raise HTTPException(status_code=403, detail="Access denied")

class CommandRequest(BaseModel):
    case_path: str

class ConfigRequest(BaseModel):
    case_path: str
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

@app.get("/cases")
def list_cases():
    """Scans for directories with a Makefile in my_cases."""
    logger.info("Listing cases")
    cases = []
    # Find Makefiles at depth 1 and 2 (e.g., Case/Makefile and Domain/Case/Makefile)
    # Using explicit depths instead of recursive=True avoids scanning large output directories
    makefiles = glob.glob(f"{CASES_DIR}/*/Makefile") + glob.glob(f"{CASES_DIR}/*/*/Makefile")
    for mk in makefiles:
        path = os.path.dirname(mk)
        rel_path = os.path.relpath(path, CASES_DIR)
        domain = rel_path.split(os.sep)[0] if os.sep in rel_path else "Uncategorized"
        name = os.path.basename(path)
        cases.append({
            "id": rel_path,
            "path": path,
            "name": name,
            "domain": domain
        })
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
                result = subprocess.run(
                    ["make"],
                    cwd=safe_path,
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
            return {"success": False, "error": str(e)}
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
                result = subprocess.run(
                    ["make", "run"],
                    cwd=safe_path,
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
            return {"success": False, "error": str(e)}
    finally:
        execution_lock.release()

@app.get("/config")
def get_config(path: str):
    """Reads the config.xml file."""
    # Validate path is within CASES_DIR for security
    safe_path = validate_case_path(path)
    logger.info(f"Reading config for: {safe_path}")

    config_path = os.path.join(safe_path, "config.xml")
    if not os.path.exists(config_path):
        logger.warning(f"Config not found: {config_path}")
        return {"content": ""}

    # Check file size to prevent DoS (memory exhaustion)
    try:
        file_size = os.path.getsize(config_path)
        if file_size > 1024 * 1024:  # 1MB limit
            logger.warning(f"Config file too large ({file_size} bytes): {config_path}")
            raise HTTPException(status_code=413, detail="File too large (limit 1MB)")
    except OSError as e:
        logger.error(f"Error checking config file size: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    with open(config_path, "r") as f:
        return {"content": f.read()}

@app.post("/config")
def save_config(req: ConfigRequest):
    """Writes the config.xml file."""
    safe_path = validate_case_path(req.case_path)
    logger.info(f"Saving config for: {safe_path} (size: {len(req.content)} bytes)")

    config_path = os.path.join(safe_path, "config.xml")
    with open(config_path, "w") as f:
        f.write(req.content)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    # Sentinel: Bind to 127.0.0.1 (localhost) by default to prevent access from external networks.
    # Allow overriding via HOST env var for Docker/remote scenarios.
    host = os.getenv("HOST", "127.0.0.1")
    uvicorn.run(app, host=host, port=8080)
