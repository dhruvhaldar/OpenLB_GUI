import os
import shutil
import pytest
from fastapi.testclient import TestClient
from backend.main import app, CASES_DIR

client = TestClient(app)

def test_ignored_dirs_are_skipped():
    # 1. Create a "tmp" directory in CASES_DIR with a Makefile
    # "tmp" is in IGNORED_DIRS in backend/main.py
    tmp_case_dir = os.path.join(CASES_DIR, "tmp")
    makefile_path = os.path.join(tmp_case_dir, "Makefile")

    os.makedirs(tmp_case_dir, exist_ok=True)
    with open(makefile_path, "w") as f:
        f.write("all:\n\techo 'test'")

    try:
        # 2. List cases
        response = client.get("/cases")
        assert response.status_code == 200
        cases = response.json()

        # 3. Verify "tmp" is NOT in the list
        # Before the fix, list_cases does NOT check IGNORED_DIRS, so this assertion should fail.
        found = any(c['name'] == 'tmp' for c in cases)
        assert not found, "Directory 'tmp' should be ignored but was found in cases list"

    finally:
        # Cleanup
        if os.path.exists(tmp_case_dir):
            shutil.rmtree(tmp_case_dir)

def test_ignored_subdirs_are_skipped():
    # Test Level 2 ignore
    # Create a domain and inside it a "tmp" case
    domain_dir = os.path.join(CASES_DIR, "TestDomain")
    tmp_sub_dir = os.path.join(domain_dir, "tmp")
    makefile_path = os.path.join(tmp_sub_dir, "Makefile")

    os.makedirs(tmp_sub_dir, exist_ok=True)
    with open(makefile_path, "w") as f:
        f.write("all:\n\techo 'test'")

    try:
        response = client.get("/cases")
        cases = response.json()

        # Check if TestDomain/tmp is present
        # path would be "TestDomain/tmp" (or with backslash on Windows)
        expected_path = os.path.join("TestDomain", "tmp")
        found = any(c['path'] == expected_path for c in cases)
        assert not found, f"Subdirectory '{expected_path}' should be ignored but was found"

    finally:
        if os.path.exists(domain_dir):
            shutil.rmtree(domain_dir)
