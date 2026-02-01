from playwright.sync_api import sync_playwright, expect
import json
import time

def test_sidebar_scroll():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock the /cases endpoint with enough cases to cause overflow
        cases = []
        for i in range(50):
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

        # 1. Filter for the last case
        print("Filtering for case-49...")
        page.fill("input[placeholder*='Filter']", "case-49")

        # Wait for list to update (only case-49 should be visible)
        page.wait_for_selector("text=case-49")

        # 2. Select it (using Enter shortcut which selects top result)
        print("Selecting case-49...")
        page.keyboard.press("Enter")

        # Verify it is selected
        selected_case = page.locator("button[aria-current='true']")
        expect(selected_case).to_contain_text("case-49")
        print("case-49 selected.")

        # 3. Clear filter to expand the list
        print("Clearing filter...")
        # The clear button appears when there is text
        page.click("button[aria-label='Clear filter']")

        # Wait for list to expand (case-0 should be visible again)
        page.wait_for_selector("text=case-0")

        # 4. Check if case-49 is visible in viewport
        print("Checking visibility of case-49...")
        # Give it a moment for scroll behavior to settle
        time.sleep(1)

        target = page.locator("button[title='case-49']")

        try:
            expect(target).to_be_in_viewport(timeout=2000)
            print("PASS: case-49 is in viewport.")
            page.screenshot(path="verification/sidebar_scrolled.png")
        except AssertionError:
            print("FAIL: case-49 is NOT in viewport.")
            page.screenshot(path="verification/scroll_fail.png")
            raise

        browser.close()

if __name__ == "__main__":
    test_sidebar_scroll()
