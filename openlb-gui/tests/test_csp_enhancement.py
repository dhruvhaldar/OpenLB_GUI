from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_enhanced_csp_headers():
    response = client.get("/cases")
    assert response.status_code == 200
    csp = response.headers.get("Content-Security-Policy", "")

    # Check for missing directives
    assert "object-src 'none'" in csp, "Missing object-src 'none' in CSP"
    assert "base-uri 'none'" in csp, "Missing base-uri 'none' in CSP"
    assert "form-action 'self'" in csp, "Missing form-action 'self' in CSP"
