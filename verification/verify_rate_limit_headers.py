
import httpx
import asyncio

# Base URL of the backend
BASE_URL = "http://127.0.0.1:8080"

async def test_rate_limit_headers():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        # Trigger rate limit for POST /cases/duplicate (limit 20)
        # We need to send 21 requests.
        # Note: We use a dummy request that would fail validation but hits the rate limiter first?
        # Actually rate limiter is checked BEFORE validation middleware?
        # Let's check main.py.
        # add_security_headers is outermost. So it runs FIRST.
        # So yes, rate limiter runs before everything else.

        print("Sending 25 requests to trigger rate limit...")
        headers_found = False
        for i in range(25):
            try:
                # We send a request that would normally fail (invalid body)
                # but we care about the 429 response.
                resp = await client.post("/cases/duplicate", json={"source_path": "foo", "new_name": "bar"})
                if resp.status_code == 429:
                    print(f"Rate limit hit at request {i+1}")
                    # Check headers
                    csp = resp.headers.get("Content-Security-Policy")
                    x_frame = resp.headers.get("X-Frame-Options")
                    print(f"429 Response Headers: {resp.headers}")

                    if csp and x_frame == "DENY":
                        print("SUCCESS: Security headers present on 429 response.")
                        headers_found = True
                    else:
                        print("FAILURE: Security headers MISSING on 429 response.")
                        exit(1)
                    break
            except Exception as e:
                print(f"Request failed: {e}")

        if not headers_found:
            print("Did not hit rate limit or didn't check headers.")
            exit(1)

if __name__ == "__main__":
    asyncio.run(test_rate_limit_headers())
