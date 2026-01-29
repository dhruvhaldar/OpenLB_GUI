from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_get_with_body_rejected():
    """
    Verifies that a GET request with a body is now REJECTED (returns 400).
    """
    # Send a GET request with a body and Content-Length
    response = client.request("GET", "/cases", content=b"A" * 100, headers={"Content-Type": "text/plain"})

    # NEW BEHAVIOR: 400 Bad Request
    assert response.status_code == 400
    assert "Request body not allowed" in response.json()['detail']

def test_delete_with_body_rejected():
    """
    Verifies that a DELETE request with a body is now REJECTED (returns 400).
    """
    response = client.request("DELETE", "/cases?case_path=nonexistent", content=b"A" * 100)

    # NEW BEHAVIOR: 400 Bad Request
    assert response.status_code == 400
    assert "Request body not allowed" in response.json()['detail']

def test_get_without_body_allowed():
    """
    Verifies that a normal GET request is still allowed.
    """
    response = client.get("/cases")
    assert response.status_code == 200
