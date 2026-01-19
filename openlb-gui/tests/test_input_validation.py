from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_delete_case_length_limit():
    """
    Test that the delete_case endpoint rejects paths that are too long.
    DoS Protection: Preventing massive strings from being processed by validation logic.
    """
    # Create a path longer than 4096 characters
    long_path = "a" * 4097

    response = client.delete(f"/cases?case_path={long_path}")

    # Expect 422 Unprocessable Entity due to validation error
    assert response.status_code == 422
    assert "string_too_long" in response.text

def test_get_config_length_limit():
    """
    Test that the get_config endpoint rejects paths that are too long.
    """
    long_path = "a" * 4097

    response = client.get(f"/config?path={long_path}")

    assert response.status_code == 422
    assert "string_too_long" in response.text

def test_content_type_enforcement():
    """
    Sentinel: Test that POST requests enforce Content-Type: application/json.
    This prevents CSRF via Simple Requests (e.g. text/plain from HTML forms).
    """
    # 1. Invalid Content-Type (text/plain)
    # Using a dummy payload and path. The middleware runs BEFORE input validation of the endpoint.
    # So we should get 415, not 422.
    response = client.post(
        "/cases/duplicate",
        headers={"Content-Type": "text/plain"},
        content='{"source_path": "a", "new_name": "b"}'
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Content-Type must be application/json"

    # 2. Missing Content-Type
    response = client.post(
        "/cases/duplicate",
        headers={"Content-Type": ""}, # Explicitly empty to override client default
        content='...'
    )
    assert response.status_code == 415
    assert response.json()["detail"] == "Content-Type must be application/json"

    # 3. Valid Content-Type (application/json)
    # This should proceed to the next checks (Content-Length, then endpoint logic).
    # Since we send invalid JSON/schema, we expect 422 from FastAPI.
    response = client.post(
        "/cases/duplicate",
        headers={"Content-Type": "application/json"},
        content='invalid-json'
    )
    # 422 Unprocessable Entity (Validation Error) means middleware PASSED
    # 400 Bad Request (JSON Decode Error) means middleware PASSED
    assert response.status_code in [400, 422]
