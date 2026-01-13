import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add backend to path
# We assume PYTHONPATH is set to include openlb-gui directory when running tests
from backend.main import app, CASES_PATH

client = TestClient(app)

@pytest.fixture
def setup_test_case():
    """Creates a temporary test case directory."""
    case_name = "test_atomic_case"
    case_path = os.path.join(CASES_PATH, case_name)
    os.makedirs(case_path, exist_ok=True)
    yield case_name
    # Cleanup
    if os.path.exists(case_path):
        shutil.rmtree(case_path)

def test_atomic_save_config(setup_test_case):
    case_name = setup_test_case
    payload = {
        "case_path": case_name,
        "content": "<xml>Atomic Content</xml>"
    }

    # Save config
    response = client.post("/config", json=payload)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Verify file exists and content matches
    config_path = os.path.join(CASES_PATH, case_name, "config.xml")
    assert os.path.exists(config_path)

    with open(config_path, "r") as f:
        content = f.read()
        assert content == payload["content"]

    # Verify permissions (if on Linux)
    if os.name == 'posix':
        mode = os.stat(config_path).st_mode
        # Check for 644 (octal 0o644)
        # S_IMODE returns the permission bits
        import stat
        assert stat.S_IMODE(mode) == 0o644
