from fastapi.testclient import TestClient
from backend.main import app
import os

client = TestClient(app)

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
