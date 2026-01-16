
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

def test_duplicate_case_excludes_artifacts(temp_cases_dir):
    """
    Verifies that duplicating a case excludes build artifacts like .o, .vtk, .log files.
    """

    # Patch the CASES_DIR and CASES_PATH in the backend
    with patch("backend.main.CASES_DIR", str(temp_cases_dir)), \
         patch("backend.main.CASES_PATH", temp_cases_dir), \
         patch("backend.main.CASES_DIR_WITH_SEP", str(temp_cases_dir) + os.sep):

        # Verify initial state
        source_path = temp_cases_dir / "test_case"
        assert (source_path / "main.o").exists()
        assert (source_path / "simulation.vtk").exists()

        # Perform duplication
        response = client.post(
            "/cases/duplicate",
            json={"source_path": "test_case", "new_name": "test_case_clean"}
        )

        assert response.status_code == 200

        # Check the new case
        new_case_path = temp_cases_dir / "test_case_clean"
        assert new_case_path.exists()

        # Essential files MUST be present
        assert (new_case_path / "Makefile").exists()
        assert (new_case_path / "config.xml").exists()
        assert (new_case_path / "main.cpp").exists()

        # Artifacts MUST be absent (this will fail before optimization)
        assert not (new_case_path / "main.o").exists(), "Object files should not be copied"
        assert not (new_case_path / "simulation.vtk").exists(), "VTK files should not be copied"
        assert not (new_case_path / "output.log").exists(), "Log files should not be copied"

        # Directories are copied recursively, but we might want to exclude tmp dirs too
        # For now, let's focus on file extensions.
