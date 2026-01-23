import os
import pytest

def test_index_html_has_csp():
    """
    Sentinel Security Check:
    Verifies that the frontend index.html includes a Content-Security-Policy meta tag.
    This protects the application from XSS, Clickjacking, and other injection attacks
    during the initial document load, before backend headers take effect (or if served statically).
    """
    # Locate index.html relative to this test file
    # openlb-gui/tests/test_frontend_csp.py -> openlb-gui/frontend/index.html
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index_path = os.path.join(base_dir, "frontend", "index.html")

    assert os.path.exists(index_path), f"index.html not found at {index_path}"

    with open(index_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Normalize content for easier checking (remove newlines/excess whitespace)
    # But simple substring check is usually enough

    # 1. Check for the meta tag existence
    assert '<meta http-equiv="Content-Security-Policy"' in content, "Missing Content-Security-Policy meta tag"

    # 2. Check for critical directives
    assert "default-src 'self'" in content, "CSP must have default-src 'self'"
    assert "object-src 'none'" in content, "CSP must disable object-src"
    assert "base-uri 'self'" in content, "CSP must restrict base-uri"
    assert "form-action 'self'" in content, "CSP must restrict form-action"

    # 3. Check for API connectivity
    # Ensure the backend URL is allowed
    assert "http://localhost:8080" in content, "CSP must allow connection to backend (localhost:8080)"

    # 4. Check for WebSocket support (Vite HMR)
    # This is needed for dev environment
    assert "ws://localhost:5173" in content, "CSP must allow WebSocket for Vite HMR"

    # 5. Check for script/style restrictions
    # We currently allow unsafe-inline due to Vite/React requirements,
    # but we ensure it's restricted to 'self' and not * (wildcard)
    assert "script-src 'self' 'unsafe-inline'" in content, "CSP script-src check failed"
    assert "style-src 'self' 'unsafe-inline'" in content, "CSP style-src check failed"
