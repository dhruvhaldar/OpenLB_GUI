from playwright.sync_api import sync_playwright, expect
import json

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
                "domain": "Fluids"
            },
            {
                "id": "case-2",
                "path": "/path/to/dam-break",
                "name": "dam-break",
                "domain": "Fluids"
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

        # Type search term "cyl"
        print("Typing search term 'cyl'...")
        page.fill("input[placeholder*='Filter']", "cyl")

        # Wait for list to update (debounced)
        page.wait_for_timeout(500)

        # Verify "cylinder-flow" is still visible
        expect(page.get_by_text("cylinder-flow")).to_be_visible()

        # Verify "dam-break" is NOT visible
        expect(page.get_by_text("dam-break")).not_to_be_visible()

        # Verify highlighting
        # We look for an element containing "cyl" that has the highlight class
        # Ideally we'd be more specific, but let's check for the strong/span with the class
        print("Verifying highlighting...")

        # The highlighted part "cyl" should be in a span with bold/blue classes
        # We need to find the specific span.
        # Since we don't have the classes yet, this test will fail if we check for them now.
        # But that's the point of a verification script - to fail first then pass.

        highlighted = page.locator("span.font-bold.text-blue-400", has_text="cyl")

        if highlighted.count() > 0:
            print("PASS: Highlighting found")
        else:
            print("FAIL: Highlighting NOT found")

        # Test special characters (Regression test for regex crash)
        print("Typing special character '('...")
        page.fill("input[placeholder*='Filter']", "(")
        page.wait_for_timeout(500)

        # If the app crashed, this element check might fail or timeout
        # We just want to ensure the app is still alive.
        # Check if the list is still visible (empty or not)
        # Using a check on the input value to ensure page is responsive
        expect(page.locator("input[placeholder*='Filter']")).to_have_value("(")
        print("PASS: App did not crash on special character")

        page.screenshot(path="verification/verify_highlight.png")
        browser.close()

if __name__ == "__main__":
    test_search_highlight()
