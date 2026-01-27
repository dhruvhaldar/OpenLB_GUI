from playwright.sync_api import sync_playwright, expect
import json
import time

def test_sidebar_count():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock the /cases endpoint
        cases = []
        for i in range(10):
            cases.append({
                "id": f"case-{i}",
                "path": f"/path/to/case-{i}",
                "name": f"case-{i}",
                "domain": "TestDomain"
            })

        def handle_cases(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(cases)
            )

        page.route("**/cases", handle_cases)
        page.route("**/config?*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({"content": "config content"})))

        # Navigate to the frontend
        print("Navigating to frontend...")
        page.goto("http://localhost:5173")

        # Wait for cases to load
        print("Waiting for cases to load...")
        page.wait_for_selector("text=case-0")

        # Verify initial count
        print("Verifying initial count...")
        count_locator = page.get_by_text("10/10")
        expect(count_locator).to_be_visible()
        print("PASS: Initial count is 10/10")

        # Filter cases
        print("Filtering cases...")
        page.fill("input[type='text']", "case-1")

        # Should match case-1 only
        # Wait a bit for debounce if any (Sidebar uses useDeferredValue which is React based, but input update is immediate)
        # Verify count updates to 1/10
        print("Verifying filtered count...")
        count_locator = page.get_by_text("1/10")
        expect(count_locator).to_be_visible()
        print("PASS: Filtered count is 1/10")

        # Clear filter
        print("Clearing filter...")
        page.fill("input[type='text']", "")

        # Verify count returns to 10/10
        print("Verifying cleared count...")
        count_locator = page.get_by_text("10/10")
        expect(count_locator).to_be_visible()
        print("PASS: Count returned to 10/10")

        page.screenshot(path="verification/verification.png")
        browser.close()

if __name__ == "__main__":
    test_sidebar_count()
