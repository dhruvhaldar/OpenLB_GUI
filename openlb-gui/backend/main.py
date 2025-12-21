from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import subprocess
import glob
from pathlib import Path

app = FastAPI()

# Allow CORS for frontend dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolve cases directory relative to the project root (2 levels up from backend/main.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CASES_DIR_PATH = PROJECT_ROOT / "my_cases"
CASES_DIR = str(CASES_DIR_PATH)

def validate_case_path(path_str: str) -> Path:
    """
    Validates that the given path is within the CASES_DIR.
    Returns the resolved Path object if valid, otherwise raises HTTPException.
    """
    try:
        target_path = Path(path_str).resolve()
        # Check if the path is relative to CASES_DIR_PATH
        if not target_path.is_relative_to(CASES_DIR_PATH):
             raise HTTPException(status_code=403, detail="Access denied")
        return target_path
    except (ValueError, RuntimeError):
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
    # Recursively find Makefiles
    makefiles = glob.glob(f"{CASES_DIR}/**/Makefile", recursive=True)
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
    target_path = validate_case_path(req.case_path)

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Case path not found")

    try:
        # Run make
        result = subprocess.run(
            ["make"],
            cwd=str(target_path),
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
    target_path = validate_case_path(req.case_path)

    if not target_path.exists():
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
            cwd=str(target_path),
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
    target_path = validate_case_path(path)

    config_path = target_path / "config.xml"
    if not config_path.exists():
        return {"content": ""}

    with open(config_path, "r") as f:
        return {"content": f.read()}

@app.post("/config")
def save_config(req: ConfigRequest):
    """Writes the config.xml file."""
    target_path = validate_case_path(req.case_path)

    config_path = target_path / "config.xml"
    with open(config_path, "w") as f:
        f.write(req.content)
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
