import shutil
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

@pytest.fixture
def mock_cases_dir(tmp_path):
    # Create a dummy case to duplicate
    src_case = tmp_path / "SourceCase"
    src_case.mkdir()
    (src_case / "config.xml").write_text("<config></config>")

    with patch("backend.main.CASES_DIR", str(tmp_path)), \
         patch("backend.main.CASES_PATH", tmp_path), \
         patch("backend.main.CASES_DIR_WITH_SEP", str(tmp_path) + os.sep):
        yield tmp_path

def test_duplicate_cleanup_on_failure(mock_cases_dir):
    # Verifies that if duplication fails midway, the target directory is cleaned up.
    target_name = "FailedCopy"
    target_path = mock_cases_dir / target_name

    if target_path.exists():
        shutil.rmtree(target_path)

    def side_effect(src, dst, **kwargs):
        os.makedirs(dst)
        (Path(dst) / "garbage.txt").touch()
        raise OSError("Disk full")

    with patch("shutil.copytree", side_effect=side_effect):
        response = client.post("/cases/duplicate", json={
            "source_path": "SourceCase",
            "new_name": target_name
        })

        assert response.status_code == 500
        assert not target_path.exists()

def test_duplicate_does_not_delete_existing_on_error(mock_cases_dir):
    # CRITICAL: If target already exists, and we get an error (e.g. FileExistsError or even subsequent error),
    # we MUST NOT delete the existing directory.

    target_name = "ExistingCase"
    target_path = mock_cases_dir / target_name
    target_path.mkdir()
    (target_path / "precious_data.txt").write_text("Do not delete me")

    # In the real app, we check os.path.exists(target_path) BEFORE copytree.
    # So we get 409 Conflict normally.
    # But if a race condition happens:
    # 1. os.path.exists -> False
    # 2. Another process creates directory
    # 3. shutil.copytree -> FileExistsError

    # Let's simulate FileExistsError from shutil.copytree
    with patch("shutil.copytree", side_effect=FileExistsError("File exists")):
        # We need to bypass the initial check in duplicate_case to reach copytree.
        # We can simulate the race condition by mocking os.path.exists to return False initially
        # BUT wait, duplicate_case calls os.path.exists.
        # If we mock os.path.exists, we might break the cleanup check too (if os.path.exists(target_path)).

        # We only want the FIRST check to return False.
        # The cleanup check 'if os.path.exists(target_path)' must return True.

        original_exists = os.path.exists

        def side_effect_exists(path):
            if str(path) == str(target_path):
                # If we are in the main body (before copytree), we want False to simulate race.
                # If we are in the exception handler, we want True.
                # This is hard to distinguish without inspecting stack or state.
                # But wait, shutil.copytree raises FileExistsError.
                pass
            return original_exists(path)

        # Easier way: Just assume os.path.exists check passes (maybe race condition).
        # We can bypass the check by patching os.path.exists to return False specifically for the check.
        # But we need it to return True for the cleanup logic.

        # Let's rely on the fact that if copytree raises FileExistsError, the dir exists.

        with patch("os.path.exists", side_effect=[False, True, True]): # First check False, subsequent True
             response = client.post("/cases/duplicate", json={
                "source_path": "SourceCase",
                "new_name": target_name
            })

             # It should catch FileExistsError and raise 500
             # BUT it should NOT delete the directory.

             assert response.status_code == 500
             assert target_path.exists(), "CRITICAL: Existing directory was DELETED!"
             assert (target_path / "precious_data.txt").exists()
