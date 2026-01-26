import os
import pytest
import shutil
import stat
import threading
import time
from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app

client = TestClient(app)

@pytest.mark.timeout(5) # Fail if hangs > 5s
def test_duplicate_fifo_dos(tmp_path):
    # Setup
    cases_dir = tmp_path / "cases"
    cases_dir.mkdir()
    source_case = cases_dir / "fifo_case"
    source_case.mkdir()
    (source_case / "Makefile").write_text("all:\n\t@echo build")
    (source_case / "config.xml").write_text("<config></config>")

    # Create FIFO
    fifo_path = source_case / "my_fifo"
    try:
        os.mkfifo(fifo_path)
    except AttributeError:
        pytest.skip("mkfifo not supported")

    # Mock backend config
    with patch("backend.main.CASES_DIR", str(cases_dir)), \
         patch("backend.main.CASES_PATH", cases_dir), \
         patch("backend.main.CASES_DIR_WITH_SEP", str(cases_dir) + os.sep):

        # Trigger duplicate
        # If vulnerable, this will hang until timeout
        # Note: shutil.copytree will block on open(fifo)
        response = client.post(
            "/cases/duplicate",
            json={"source_path": "fifo_case", "new_name": "fifo_case_copy"}
        )

        assert response.status_code == 200

        # Verify result
        new_case = cases_dir / "fifo_case_copy"
        assert new_case.exists()
        assert (new_case / "Makefile").exists()
        # FIFO should NOT be copied (or at least not hang)
        # With safe_copy, it should be skipped.
        assert not (new_case / "my_fifo").exists(), "FIFO was copied (should be skipped)"
