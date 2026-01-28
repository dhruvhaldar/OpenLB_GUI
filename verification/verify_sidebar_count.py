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
        # The count should be 10
        print("Verifying initial count...")
        count_locator = page.get_by_label("10 of 10 cases shown")
        expect(count_locator).to_be_visible()
        expect(count_locator).to_have_text("10")
        print("Initial count verified: 10")

        # Filter cases
        print("Filtering cases...")
        page.fill("input[placeholder*='Filter cases']", "case-1")

        # "case-1" matches "case-1".
        # So count should be 1.

        # Verify filtered count
        print("Verifying filtered count...")
        filtered_count_locator = page.get_by_label("1 of 10 cases shown")
        expect(filtered_count_locator).to_be_visible()
        expect(filtered_count_locator).to_have_text("1/10")
        print("Filtered count verified: 1/10")

        page.screenshot(path="verification/sidebar_count.png")
        browser.close()

if __name__ == "__main__":
    test_sidebar_count()
