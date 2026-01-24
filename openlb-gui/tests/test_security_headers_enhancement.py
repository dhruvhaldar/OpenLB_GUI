from fastapi.testclient import TestClient
from backend.main import app
import pytest

client = TestClient(app)

def test_security_headers_present():
    """
    Verifies that X-Permitted-Cross-Domain-Policies and Cross-Origin-Opener-Policy
    are correctly set on responses.
    """
    # We use a non-existent path to ensure we hit the middleware
    # but don't depend on specific business logic or auth.
    # The middleware should apply headers even to 404 responses.
    response = client.get("/non-existent-path-for-security-test")

    # We expect 404, but we only care about headers here.
    # The middleware runs after the response is generated.

    # Check for X-Permitted-Cross-Domain-Policies
    xpcdp = response.headers.get("X-Permitted-Cross-Domain-Policies")
    assert xpcdp == "none", \
        f"X-Permitted-Cross-Domain-Policies should be 'none', got: {xpcdp}"

    # Check for Cross-Origin-Opener-Policy
    coop = response.headers.get("Cross-Origin-Opener-Policy")
    assert coop == "same-origin", \
        f"Cross-Origin-Opener-Policy should be 'same-origin', got: {coop}"
