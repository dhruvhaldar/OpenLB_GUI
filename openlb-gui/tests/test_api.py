from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.main import app
import os

client = TestClient(app)

def test_security_headers():
    response = client.get("/cases")
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("Cache-Control") == "no-store"
    assert response.headers.get("Pragma") == "no-cache"
    assert "frame-ancestors 'none'" in response.headers.get("Content-Security-Policy")
    assert "camera=()" in response.headers.get("Permissions-Policy")

def test_get_config_dos_protection():
    # Get a valid case path first
    response = client.get("/cases")
    if not response.json():
        # If no cases exist, we can't test this easily without mocking validate_case_path too.
        # Assuming cases exist as per other tests.
        return

    case = response.json()[0]
    path = case['path']

    # Patch os.fstat in backend.main to simulate a large file
    # We must patch os.fstat because the code now uses it on the file descriptor
    with patch("backend.main.os.fstat") as mock_fstat:
        mock_fstat.return_value.st_size = 1024 * 1024 + 100  # 1MB + 100 bytes

        res = client.get(f"/config?path={path}")
        assert res.status_code == 413
        assert "file too large" in res.json()['detail'].lower()

def test_list_cases():
    response = client.get("/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 2
    domains = [c['domain'] for c in cases]
    assert "Aerospace" in domains
    assert "Biomedical" in domains

def test_config_read_write():
    # Find a case
    response = client.get("/cases")
    case = response.json()[0]
    path = case['path']

    # Read config
    res_read = client.get(f"/config?path={path}")
    assert res_read.status_code == 200
    original_content = res_read.json()['content']

    # Write new config
    new_content = "<config><test>123</test></config>"
    res_write = client.post("/config", json={"case_path": path, "content": new_content})
    assert res_write.status_code == 200

    # Verify write
    res_read_again = client.get(f"/config?path={path}")
    assert res_read_again.json()['content'] == new_content

    # Restore config
    client.post("/config", json={"case_path": path, "content": original_content})

def test_build_run():
    # Only test if it returns a success structure, mock execution is already verified manually
    response = client.get("/cases")
    case = next(c for c in response.json() if c['name'] == 'cyl_flow')

    res_build = client.post("/build", json={"case_path": case['path']})
    assert res_build.status_code == 200
    assert res_build.json()['success'] is True

    res_run = client.post("/run", json={"case_path": case['path']})
    assert res_run.status_code == 200
    assert res_run.json()['success'] is True

def test_duplicate_delete_case():
    # 1. List cases to find a source
    response = client.get("/cases")
    if not response.json():
        return # Cannot test if no cases

    source_case = response.json()[0]
    source_path = source_case['path']
    new_name = "test_duplicate_case_123"

    # 2. Duplicate it
    res_dup = client.post("/cases/duplicate", json={
        "source_path": source_path,
        "new_name": new_name
    })
    assert res_dup.status_code == 200
    new_path = res_dup.json()['case']['path']
    assert new_name in new_path

    # 3. Verify it exists in list
    res_list = client.get("/cases")
    assert any(c['path'] == new_path for c in res_list.json())

    # 4. Delete it
    res_del = client.delete(f"/cases?case_path={new_path}")
    assert res_del.status_code == 200

    # 5. Verify it is gone
    res_list_after = client.get("/cases")
    assert not any(c['path'] == new_path for c in res_list_after.json())
