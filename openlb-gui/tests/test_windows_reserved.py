from fastapi.testclient import TestClient
from backend.main import app
import shutil
import os
import pytest

client = TestClient(app)

@pytest.fixture
def clean_env():
    # Setup
    source_path = os.path.abspath("my_cases/test_source_reserved")
    os.makedirs(source_path, exist_ok=True)
    with open(os.path.join(source_path, "Makefile"), "w") as f:
        f.write("all:\n\techo hello")

    yield "test_source_reserved"

    # Teardown
    if os.path.exists(source_path):
        shutil.rmtree(source_path)

    # Remove the target if it was created
    target_path = os.path.abspath("my_cases/COM1")
    if os.path.exists(target_path):
        shutil.rmtree(target_path)

    target_path_aux = os.path.abspath("my_cases/AUX")
    if os.path.exists(target_path_aux):
        shutil.rmtree(target_path_aux)

    target_path_aux_lower = os.path.abspath("my_cases/aux")
    if os.path.exists(target_path_aux_lower):
        shutil.rmtree(target_path_aux_lower)

def test_duplicate_reserved_name(clean_env):
    source_name = clean_env

    # Try to duplicate to "COM1"
    response = client.post("/cases/duplicate", json={
        "source_path": source_name,
        "new_name": "COM1"
    })

    # Currently this passes (200), but we want it to fail (400)
    # So we assert 400. This test will FAIL initially.
    assert response.status_code == 400, f"Expected 400 Bad Request for reserved name, got {response.status_code}"
    assert "reserved" in response.json()['detail'].lower()

def test_duplicate_reserved_name_case_insensitive(clean_env):
    source_name = clean_env

    # Try to duplicate to "aux" (lowercase)
    response = client.post("/cases/duplicate", json={
        "source_path": source_name,
        "new_name": "aux"
    })

    assert response.status_code == 400
    assert "reserved" in response.json()['detail'].lower()

def test_duplicate_reserved_name_clock(clean_env):
    source_name = clean_env

    # Try to duplicate to "CLOCK$"
    response = client.post("/cases/duplicate", json={
        "source_path": source_name,
        "new_name": "CLOCK$"
    })

    assert response.status_code == 400
    detail = response.json()['detail'].lower()
    # CLOCK$ is blocked by the regex (due to '$') before the reserved check.
    # We accept either error message as proof of blocking.
    assert "reserved" in detail or "invalid name" in detail
