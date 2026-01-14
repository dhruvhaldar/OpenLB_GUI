from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_delete_case_max_length():
    # Generate a path longer than 4096 characters
    long_path = "a" * 4097
    response = client.delete(f"/cases?case_path={long_path}")
    # Expect 422 Unprocessable Entity due to validation error
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"

def test_get_config_max_length():
    # Generate a path longer than 4096 characters
    long_path = "a" * 4097
    response = client.get(f"/config?path={long_path}")
    # Expect 422 Unprocessable Entity due to validation error
    assert response.status_code == 422, f"Expected 422, got {response.status_code}"
