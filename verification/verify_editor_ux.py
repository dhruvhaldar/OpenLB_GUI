from playwright.sync_api import sync_playwright, expect
import json
import time

def test_config_editor_ux():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock the /cases endpoint
        cases = [{
            "id": "case-1",
            "path": "/path/to/case-1",
            "name": "case-1",
            "domain": "TestDomain"
        }]

        def handle_cases(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(cases)
            )

        # Mock the /config endpoint
        def handle_config(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"content": "key: value\n"})
            )

        page.route("**/cases", handle_cases)
        page.route("**/config?*", handle_config)

        # Navigate to the frontend
        print("Navigating to frontend...")
        page.goto("http://localhost:5173")

        # Wait for cases to load
        print("Waiting for cases to load...")
        page.wait_for_selector("text=case-1")

        # Select the case
        print("Selecting case-1...")
        page.click("text=case-1")

        # Wait for config editor to be visible (it loads config)
        # The textarea inside ConfigEditor
        print("Waiting for ConfigEditor...")
        page.wait_for_selector("textarea")

        # Click textarea to focus
        print("Focusing textarea...")
        page.click("textarea")

        # Type some text
        print("Typing 'new_key:'...")
        page.keyboard.type("new_key:")

        # Press Tab
        print("Pressing Tab...")
        page.keyboard.press("Tab")

        # Check if focus is still on textarea
        print("Checking focus...")
        is_focused = page.evaluate("document.activeElement.tagName === 'TEXTAREA'")

        if not is_focused:
            print("FAILURE: Focus moved away from textarea after pressing Tab (Expected behavior for now).")
        else:
            print("SUCCESS: Focus remained in textarea.")

        # Check content
        content = page.input_value("textarea")
        print(f"Content: {repr(content)}")

        # Verify indentation (assuming we expected 2 spaces)
        if "new_key:  " in content:
             print("SUCCESS: Tab inserted 2 spaces.")
        else:
             print("FAILURE: Tab did not insert 2 spaces.")

        # Now test Escape
        print("Focusing textarea again (if lost)...")
        page.click("textarea")

        print("Pressing Escape...")
        page.keyboard.press("Escape")

        is_focused_after_esc = page.evaluate("document.activeElement.tagName === 'TEXTAREA'")
        if not is_focused_after_esc:
            print("SUCCESS: Escape blurred the textarea.")
        else:
            print("FAILURE: Escape did not blur the textarea.")

        # Take screenshot of the ConfigEditor with the new hint
        print("Taking screenshot...")
        page.screenshot(path="verification/config_editor_ux.png")

        browser.close()

if __name__ == "__main__":
    test_config_editor_ux()
