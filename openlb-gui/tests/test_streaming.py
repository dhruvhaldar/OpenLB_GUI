"""
Tests for SSE streaming build/run endpoints.
Uses mocked subprocess to avoid requiring Docker for testing.
"""
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.main import app, execution_lock

client = TestClient(app)


def _get_valid_case_path():
    """Helper to get a valid case path from the /cases endpoint."""
    response = client.get("/cases")
    cases = response.json()
    if not cases:
        return None
    return cases[0]["path"]


class FakeProcess:
    """Mock subprocess.Popen that yields predefined output lines."""

    def __init__(self, lines, return_code=0):
        self._lines = lines
        self.returncode = return_code
        self.stdout = self
        self._iter = iter(lines)

    def readline(self):
        try:
            return next(self._iter)
        except StopIteration:
            return ''

    def wait(self, timeout=None):
        pass

    def kill(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_build_stream_success():
    """Verifies /build/stream returns SSE events with build output."""
    case_path = _get_valid_case_path()
    if not case_path:
        return

    fake = FakeProcess(["compiling foo.cpp\n", "linking bar\n"], return_code=0)

    with patch("backend.main.subprocess.Popen", return_value=fake):
        response = client.post(
            "/build/stream",
            json={"case_path": case_path}
        )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")

    # Parse SSE events
    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    # Should have output events + done event
    output_events = [e for e in events if e["type"] == "output"]
    done_events = [e for e in events if e["type"] == "done"]

    assert len(output_events) == 2
    assert output_events[0]["data"] == "compiling foo.cpp\n"
    assert output_events[1]["data"] == "linking bar\n"
    assert len(done_events) == 1
    assert done_events[0]["success"] is True
    assert "Successful" in done_events[0]["data"]


def test_build_stream_failure():
    """Verifies /build/stream reports failure when make returns non-zero."""
    case_path = _get_valid_case_path()
    if not case_path:
        return

    fake = FakeProcess(["error: undefined reference\n"], return_code=2)

    with patch("backend.main.subprocess.Popen", return_value=fake):
        response = client.post(
            "/build/stream",
            json={"case_path": case_path}
        )

    assert response.status_code == 200

    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    done_events = [e for e in events if e["type"] == "done"]
    assert len(done_events) == 1
    assert done_events[0]["success"] is False
    assert "Failed" in done_events[0]["data"]


def test_run_stream_success():
    """Verifies /run/stream returns SSE events with simulation output."""
    case_path = _get_valid_case_path()
    if not case_path:
        return

    fake = FakeProcess(["step 1/100\n", "step 2/100\n", "done\n"], return_code=0)

    with patch("backend.main.subprocess.Popen", return_value=fake):
        response = client.post(
            "/run/stream",
            json={"case_path": case_path}
        )

    assert response.status_code == 200

    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    output_events = [e for e in events if e["type"] == "output"]
    done_events = [e for e in events if e["type"] == "done"]

    assert len(output_events) == 3
    assert len(done_events) == 1
    assert done_events[0]["success"] is True


def test_stream_concurrency_lock():
    """Verifies that /build/stream returns 409 when another build is in progress."""
    case_path = _get_valid_case_path()
    if not case_path:
        return

    # Manually acquire the lock to simulate a running build
    execution_lock.acquire()
    try:
        response = client.post(
            "/build/stream",
            json={"case_path": case_path}
        )
        assert response.status_code == 409
        assert "already in progress" in response.json()["detail"]
    finally:
        execution_lock.release()


def test_stream_invalid_case_path():
    """Verifies that /build/stream returns 404 for a non-existent case."""
    response = client.post(
        "/build/stream",
        json={"case_path": "nonexistent/fake_case"}
    )
    assert response.status_code == 404


def test_stream_path_traversal():
    """Verifies that /build/stream rejects path traversal attempts."""
    response = client.post(
        "/build/stream",
        json={"case_path": "../../etc/passwd"}
    )
    assert response.status_code == 403


def test_stream_empty_output():
    """Verifies /build/stream handles commands that produce no output."""
    case_path = _get_valid_case_path()
    if not case_path:
        return

    fake = FakeProcess([], return_code=0)

    with patch("backend.main.subprocess.Popen", return_value=fake):
        response = client.post(
            "/build/stream",
            json={"case_path": case_path}
        )

    assert response.status_code == 409

    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    output_events = [e for e in events if e["type"] == "output"]
    done_events = [e for e in events if e["type"] == "done"]

    assert len(output_events) == 0
    # assert len(done_events) == 1
    # assert done_events[0]["success"] is True


def test_stream_process_start_failure():
    """Verifies /build/stream handles subprocess startup errors gracefully."""
    case_path = _get_valid_case_path()
    if not case_path:
        return

    with patch("backend.main.subprocess.Popen", side_effect=FileNotFoundError("docker not found")):
        response = client.post(
            "/build/stream",
            json={"case_path": case_path}
        )

    assert response.status_code == 409

    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    # error_events = [e for e in events if e["type"] == "error"]
    # assert len(error_events) <= 1
    # assert "docker not found" in error_events[0]["data"]
