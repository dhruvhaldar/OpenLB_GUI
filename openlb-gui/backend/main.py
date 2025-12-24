from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import glob
from pathlib import Path

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

# Resolve cases directory relative to the project root (2 levels up from backend/main.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
# Use resolve() for CASES_DIR to ensure we have the absolute path
CASES_PATH = (PROJECT_ROOT / "my_cases").resolve()
# Keep CASES_DIR as string for glob/compat but use CASES_PATH for security checks
CASES_DIR = str(CASES_PATH)

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
             raise HTTPException(status_code=403, detail="Access denied")

        return str(target_path)
    except (ValueError, RuntimeError):
        # Handle cases where is_relative_to might fail or other path errors
        raise HTTPException(status_code=403, detail="Access denied")

class CommandRequest(BaseModel):
    case_path: str

class ConfigRequest(BaseModel):
    case_path: str
    content: str

@app.get("/cases")
def list_cases():
    """Scans for directories with a Makefile in my_cases."""
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
    # Security check
    safe_path = validate_case_path(req.case_path)

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Case path not found")

    try:
        # Run make
        result = subprocess.run(
            ["make"],
            cwd=safe_path,
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/run")
def run_case(req: CommandRequest):
    """Executes 'make run' in the directory."""
    # Security check
    safe_path = validate_case_path(req.case_path)

    if not os.path.exists(safe_path):
        raise HTTPException(status_code=404, detail="Case path not found")

    try:
        # Run make run
        # Using subprocess.Popen could be better for streaming, but for now we capture output
        # Or better yet, we can stream the output if we use websockets, but for simplicity
        # let's just return the output.
        # Wait, long running simulations...
        # For a production app, we would background this and stream logs.
        # For this prototype, I will just run it and return output.

        result = subprocess.run(
            ["make", "run"],
            cwd=safe_path,
            capture_output=True,
            text=True,
            check=False
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/config")
def get_config(path: str):
    """Reads the config.xml file."""
    # Validate path is within CASES_DIR for security
    safe_path = validate_case_path(path)

    config_path = os.path.join(safe_path, "config.xml")
    if not os.path.exists(config_path):
        return {"content": ""}

    with open(config_path, "r") as f:
        return {"content": f.read()}

@app.post("/config")
def save_config(req: ConfigRequest):
    """Writes the config.xml file."""
    safe_path = validate_case_path(req.case_path)

    config_path = os.path.join(safe_path, "config.xml")
    with open(config_path, "w") as f:
        f.write(req.content)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
