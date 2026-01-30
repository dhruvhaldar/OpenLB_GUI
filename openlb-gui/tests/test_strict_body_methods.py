from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_with_body():
    """
    Verifies that a GET request with a body is rejected with 400.
    """
    # Use client.request to allow passing 'content' to GET
    response = client.request("GET", "/cases", content='{"foo": "bar"}', headers={"Content-Type": "application/json"})
    assert response.status_code == 400
    assert "Request body not allowed" in response.json()['detail']

def test_delete_with_body():
    """
    Verifies that a DELETE request with a body is rejected with 400.
    """
    # Use client.request to allow passing 'content' to DELETE
    response = client.request("DELETE", "/cases", content='{"foo": "bar"}', headers={"Content-Type": "application/json"}, params={"case_path": "foo"})
    assert response.status_code == 400
    assert "Request body not allowed" in response.json()['detail']

def test_get_without_body():
    """
    Verifies that a normal GET request is accepted.
    """
    response = client.get("/cases")
    assert response.status_code == 200

def test_delete_without_body():
    """
    Verifies that a normal DELETE request works (should return 404 for non-existent case, but NOT 400 for body).
    """
    response = client.delete("/cases", params={"case_path": "nonexistent_case_for_test"})
    assert response.status_code == 404 # Case not found, but middleware passed
    assert response.json()['detail'] == "Case not found"

def test_get_with_transfer_encoding():
    """
    Verifies that a GET request with Transfer-Encoding is rejected.
    """
    # We set the header explicitly.
    response = client.get("/cases", headers={"Transfer-Encoding": "chunked"})
    assert response.status_code == 400
    assert "Request body not allowed" in response.json()['detail']
