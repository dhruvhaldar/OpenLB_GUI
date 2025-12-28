from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app
import time
import threading
import pytest

client = TestClient(app)

def test_concurrent_builds_rejected():
    # We will mock subprocess.run to sleep for a bit to simulate a long build
    with patch("backend.main.subprocess.run") as mock_run:
        # Simulate a 1 second build
        def delayed_run(*args, **kwargs):
            time.sleep(0.5)
            class MockResult:
                returncode = 0
            return MockResult()

        mock_run.side_effect = delayed_run

        # We need a case path
        case_path = "/tmp/fake/path"

        with patch("backend.main.validate_case_path") as mock_validate:
            mock_validate.return_value = case_path
            with patch("backend.main.os.path.exists") as mock_exists:
                mock_exists.return_value = True

                results = []
                def make_request():
                    res = client.post("/build", json={"case_path": case_path})
                    results.append(res.status_code)

                # Start two threads to make concurrent requests
                t1 = threading.Thread(target=make_request)
                t2 = threading.Thread(target=make_request)

                t1.start()
                t2.start()
                t1.join()
                t2.join()

                # One should succeed (200), one should fail (409)
                assert 200 in results
                assert 409 in results

def test_concurrent_run_rejected():
     # Same test for /run endpoint
    with patch("backend.main.subprocess.run") as mock_run:
        def delayed_run(*args, **kwargs):
            time.sleep(0.5)
            class MockResult:
                returncode = 0
            return MockResult()

        mock_run.side_effect = delayed_run
        case_path = "/tmp/fake/path"

        with patch("backend.main.validate_case_path") as mock_validate:
            mock_validate.return_value = case_path
            with patch("backend.main.os.path.exists") as mock_exists:
                mock_exists.return_value = True

                results = []
                def make_request():
                    res = client.post("/run", json={"case_path": case_path})
                    results.append(res.status_code)

                t1 = threading.Thread(target=make_request)
                t2 = threading.Thread(target=make_request)

                t1.start()
                t2.start()
                t1.join()
                t2.join()

                assert 200 in results
                assert 409 in results
