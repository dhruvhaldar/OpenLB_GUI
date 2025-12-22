import sys
import os
from pathlib import Path
from fastapi.testclient import TestClient
import pytest

# Add backend to path so we can import main
sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import app, CASES_DIR

client = TestClient(app)

def test_path_traversal_sibling():
    """
    Test that accessing a sibling directory with a name starting with the same prefix
    as CASES_DIR is forbidden.
    Example: CASES_DIR = /foo/bar
             Attacker tries /foo/bar_suffix
             startswith(/foo/bar) is True, so it bypasses the check if not fixed.
    """
    # Construct a path that starts with CASES_DIR but is not inside it
    sibling_path = CASES_DIR + "_suffix"

    # We use the /config endpoint as it has the vulnerable check
    response = client.get(f"/config?path={sibling_path}")

    # Expect 403 Forbidden. If 200, it means the check was bypassed (even if file not found, it returns 200 empty dict)
    assert response.status_code == 403, f"Vulnerable to path traversal! Status: {response.status_code}, Body: {response.text}"

def test_path_traversal_parent():
    """Test that accessing the parent directory is forbidden."""
    parent_path = str(Path(CASES_DIR).parent)
    response = client.get(f"/config?path={parent_path}")
    assert response.status_code == 403

def test_valid_path():
    """Test that accessing a valid path inside CASES_DIR is allowed."""
    # We can use CASES_DIR itself
    response = client.get(f"/config?path={CASES_DIR}")
    # Should be 200 OK (empty content if no config.xml, but access allowed)
    assert response.status_code == 200
