from playwright.sync_api import sync_playwright, expect
import json
import time

def test_sidebar_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock the /cases endpoint
        cases = []
        for i in range(1000):
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

        # Click the search input to reset focus context
        print("Clicking search input...")
        page.click("input[type='text']")

        # Press ArrowDown - should focus the first case (index 0)
        print("Pressing ArrowDown (Focus 1st case)...")
        page.keyboard.press("ArrowDown")

        # Verify focus is on the first button
        # We check active element's text content
        active_text = page.evaluate("document.activeElement.textContent")
        print(f"Active element text: {active_text}")
        if "case-0" not in active_text:
             print("FAIL: Expected focus on case-0")
        else:
             print("PASS: Focus on case-0")

        # Press ArrowDown - should focus the second case (index 1)
        print("Pressing ArrowDown (Focus 2nd case)...")
        page.keyboard.press("ArrowDown")

        active_text = page.evaluate("document.activeElement.textContent")
        print(f"Active element text: {active_text}")
        if "case-1" not in active_text:
             print("FAIL: Expected focus on case-1")
        else:
             print("PASS: Focus on case-1")

        # Press End - should focus the last case (index 999)
        print("Pressing End (Focus last case)...")
        page.keyboard.press("End")

        active_text = page.evaluate("document.activeElement.textContent")
        print(f"Active element text: {active_text}")
        if "case-999" not in active_text:
             print("FAIL: Expected focus on case-999")
        else:
             print("PASS: Focus on case-999")

        # Press Home - should focus the first case
        print("Pressing Home (Focus 1st case)...")
        page.keyboard.press("Home")

        active_text = page.evaluate("document.activeElement.textContent")
        print(f"Active element text: {active_text}")
        if "case-0" not in active_text:
             print("FAIL: Expected focus on case-0")
        else:
             print("PASS: Focus on case-0")

        page.screenshot(path="verification/verification.png")
        browser.close()

if __name__ == "__main__":
    test_sidebar_navigation()
