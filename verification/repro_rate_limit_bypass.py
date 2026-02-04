import sys
import os
import unittest
from fastapi.testclient import TestClient

# Adjust path to import backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../openlb-gui/backend")))

from main import app, read_rate_limiter

class TestRateLimitBypass(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # Clear rate limiter
        read_rate_limiter.requests.clear()

    def test_head_bypass(self):
        # 1. Verify GET is limited
        print("Sending 105 GET requests...")
        blocked = False
        for i in range(105):
            response = self.client.get("/cases")
            if response.status_code == 429:
                print(f"GET blocked at request {i+1}")
                blocked = True
                break

        if not blocked:
             self.fail("GET requests were NOT blocked. Test environment issue.")

        # 2. Reset rate limiter
        read_rate_limiter.requests.clear()

        # 3. Send 105 HEAD requests
        print("Sending 105 HEAD requests...")
        head_blocked = False
        for i in range(105):
            response = self.client.head("/cases")
            if response.status_code == 429:
                print(f"HEAD blocked at request {i+1}")
                head_blocked = True
                break

        if not head_blocked:
            self.fail("HEAD requests were NOT blocked. Vulnerability persists!")
        else:
            print("SUCCESS: HEAD requests were correctly rate limited!")

if __name__ == "__main__":
    unittest.main()
