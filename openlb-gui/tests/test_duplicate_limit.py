
import os
import shutil
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from pathlib import Path

# Adjust import based on where the test file is located relative to backend
from backend.main import app

client = TestClient(app)

@pytest.fixture
def temp_cases_dir(tmp_path):
    """Creates a temporary cases directory with a sample case."""
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()

    # Create a source case "test_case"
    source_case = cases_dir / "test_case"
    source_case.mkdir()

    # Create essential files
    (source_case / "Makefile").write_text("all:\n\t@echo build")
    (source_case / "config.xml").write_text("<config></config>")
    (source_case / "main.cpp").write_text("int main() { return 0; }")

    # Create "junk" files (build artifacts)
    (source_case / "main.o").write_text("binary garbage")
    (source_case / "simulation.vtk").write_text("huge simulation data " * 100)
    (source_case / "output.log").write_text("simulation log")
    (source_case / "temp_stuff").mkdir()
    (source_case / "temp_stuff" / "trash.tmp").write_text("trash")

    return cases_dir

def test_duplicate_case_limit_files(temp_cases_dir):
    """
    Verifies that duplication fails if the source case has too many files.
    """
    # Patch limits to be very low
    # The case has Makefile, config.xml, main.cpp which are VALID (3 files).
    # It has artifacts which should be IGNORED by check_directory_limits too.
    # So valid count is 3. We set limit to 2.

    with patch("backend.main.CASES_DIR", str(temp_cases_dir)), \
         patch("backend.main.CASES_PATH", temp_cases_dir), \
         patch("backend.main.CASES_DIR_WITH_SEP", str(temp_cases_dir) + os.sep), \
         patch("backend.main.MAX_CASE_FILES", 2):

        response = client.post(
            "/cases/duplicate",
            json={"source_path": "test_case", "new_name": "test_case_dup_files"}
        )
        assert response.status_code == 413, "Should fail due to file count limit"
        assert "too many files" in response.json()['detail']

def test_duplicate_case_limit_size(temp_cases_dir):
    """
    Verifies that duplication fails if the source case is too large.
    """
    # Valid files total size is small (< 1KB).
    # Set limit to 1 byte.

    with patch("backend.main.CASES_DIR", str(temp_cases_dir)), \
         patch("backend.main.CASES_PATH", temp_cases_dir), \
         patch("backend.main.CASES_DIR_WITH_SEP", str(temp_cases_dir) + os.sep), \
         patch("backend.main.MAX_CASE_SIZE", 1): # 1 Byte limit

        response = client.post(
            "/cases/duplicate",
            json={"source_path": "test_case", "new_name": "test_case_dup_size"}
        )
        assert response.status_code == 413, "Should fail due to size limit"
        assert "too large" in response.json()['detail']

def test_duplicate_case_within_limits(temp_cases_dir):
    """
    Verifies that duplication works when within limits.
    """
    # Set limits high enough
    with patch("backend.main.CASES_DIR", str(temp_cases_dir)), \
         patch("backend.main.CASES_PATH", temp_cases_dir), \
         patch("backend.main.CASES_DIR_WITH_SEP", str(temp_cases_dir) + os.sep), \
         patch("backend.main.MAX_CASE_FILES", 10), \
         patch("backend.main.MAX_CASE_SIZE", 1024 * 1024):

        response = client.post(
            "/cases/duplicate",
            json={"source_path": "test_case", "new_name": "test_case_ok"}
        )
        assert response.status_code == 200, "Should succeed"
        assert (temp_cases_dir / "test_case_ok" / "Makefile").exists()
