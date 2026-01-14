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
