from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_invalid_content_length_string():
    # Test with non-numeric Content-Length
    # We bypass the client's auto-calculation by overriding headers
    headers = {"Content-Length": "invalid", "Content-Type": "application/json"}

    # In TestClient, unhandled exceptions in the app raise directly in the test client unless suppressed.
    # We expect the app to handle it gracefully and return 400.
    response = client.post("/cases/duplicate", headers=headers, json={"source_path": "foo", "new_name": "bar"})
    assert response.status_code == 400
    assert "Invalid Content-Length" in response.json()["detail"]

def test_negative_content_length():
    # Test with negative Content-Length
    headers = {"Content-Length": "-1", "Content-Type": "application/json"}

    response = client.post("/cases/duplicate", headers=headers, json={"source_path": "foo", "new_name": "bar"})
    assert response.status_code == 400
    assert "Invalid Content-Length" in response.json()["detail"]
