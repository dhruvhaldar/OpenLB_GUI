from playwright.sync_api import sync_playwright, expect
import json
import time

def test_search_highlight():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock the /cases endpoint
        cases = [
            {
                "id": "case-1",
                "path": "/path/to/cylinder-flow",
                "name": "cylinder-flow",
                "domain": "FluidDynamics"
            },
            {
                "id": "case-2",
                "path": "/path/to/heat-transfer",
                "name": "heat-transfer",
                "domain": "Thermodynamics"
            }
        ]

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
        page.wait_for_selector("text=cylinder-flow")

        # Type in search box
        print("Typing 'flow' in search box...")
        page.fill("input[placeholder*='Filter cases']", "flow")

        # Verify highlighting
        print("Verifying highlight...")
        item = page.locator("button[title='cylinder-flow']")

        # Check if it contains a span with text "flow" and class "font-bold"
        highlight = item.locator("span.font-bold", has_text="flow")
        expect(highlight).to_be_visible()

        # Verify 'cylinder-' is NOT highlighted (should not be in the span)
        # We can check the text content of the parent span.
        # But simpler: check that 'cylinder-' is visible and NOT inside the bold span.
        # This is implicit if the bold span only contains 'flow'.

        # Take screenshot
        print("Taking screenshot...")
        page.screenshot(path="verification/search_highlight.png")

        browser.close()

if __name__ == "__main__":
    test_search_highlight()
