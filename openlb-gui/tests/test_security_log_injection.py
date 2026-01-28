from fastapi.testclient import TestClient
from backend.main import app
import pytest
import logging

client = TestClient(app)

def test_log_injection_prevention(caplog):
    """
    Verifies that paths with control characters (like newlines) are rejected
    and do not cause log injection.
    """
    # Payload with a newline character
    malicious_path = "my_cases/legit_case\nERROR: SYSTEM COMPROMISED"

    # We expect a 400 Bad Request
    response = client.post("/build", json={"case_path": malicious_path})
    assert response.status_code == 400
    assert "Invalid characters in path" in response.json()['detail']

    # Verify that the malicious payload was NOT logged as a raw string
    # caplog captures logs. We check if the raw newline was injected.
    # The application logs using repr(), so the newline should be escaped as \n.

    found_injection = False
    for record in caplog.records:
        if "ERROR: SYSTEM COMPROMISED" in record.message:
            # If the message contains the injected text, it MUST be part of a repr() string
            # i.e., it should look like '...\\nERROR: ...' or be on the same line as "Invalid characters"
            # It should NOT be a standalone log message.
            if record.levelname == "ERROR" and record.message == "SYSTEM COMPROMISED":
                found_injection = True

    assert not found_injection, "Log Injection detected! A fake log entry was successfully created."

    # Verify we actually logged the attempt safely
    # Check for the warning with the escaped string
    assert any("Invalid characters in path" in r.message and "\\n" in r.message for r in caplog.records)

def test_del_injection_prevention(caplog):
    """
    Verifies that paths with DEL characters (\x7f) are rejected
    and do not cause log injection.
    """
    # Payload with a DEL character
    malicious_path = "my_cases/legit_case\x7fINJECTED"

    # We expect a 400 Bad Request
    response = client.post("/build", json={"case_path": malicious_path})
    assert response.status_code == 400
    assert "Invalid characters in path" in response.json()['detail']

    # Verify we logged the attempt safely (using repr, so \x7f should show up as escaped)
    assert any("Invalid characters in path" in r.message and "\\x7f" in r.message for r in caplog.records)
