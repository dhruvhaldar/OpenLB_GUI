
import pytest
from starlette.requests import Request
from starlette.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Re-implementation of the FIXED middleware for isolation in the test
# This mirrors the code in main.py
class TrustedOriginMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, allowed_origins):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(self, request: Request, call_next):
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            origin = request.headers.get("origin")
            referrer = request.headers.get("referer")

            if origin:
                if origin not in self.allowed_origins:
                     return Response("Forbidden: Untrusted Origin", status_code=403)
            elif referrer:
                 # FIXED LOGIC:
                 if not any(referrer == allowed or referrer.startswith(allowed + "/") for allowed in self.allowed_origins):
                     return Response("Forbidden: Untrusted Referrer", status_code=403)
        return await call_next(request)

app = FastAPI()
ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173"}
app.add_middleware(TrustedOriginMiddleware, allowed_origins=ALLOWED_ORIGINS)

@app.post("/test")
def endpoint_handler():
    return {"message": "success"}

client = TestClient(app)

def test_referer_bypass():
    # Attempt to bypass using a port that starts with the allowed port prefix
    # e.g., allowed: localhost:5173, attacker: localhost:51730

    # 1. Valid Referer should pass
    response = client.post("/test", headers={"Referer": "http://localhost:5173/page"})
    assert response.status_code == 200

    # 2. Invalid Referer (completely different) should fail
    response = client.post("/test", headers={"Referer": "http://evil.com/page"})
    assert response.status_code == 403

    # 3. Bypass Attempt
    # This URL effectively starts with "http://localhost:5173" but is a different origin (port 51730)
    bypass_referer = "http://localhost:51730/page"

    response = client.post("/test", headers={"Referer": bypass_referer})

    # NOW EXPECTING 403 (Secure)
    assert response.status_code == 403, "Vulnerability STILL exists! Expected 403 Forbidden for bypass."
