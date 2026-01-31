from playwright.sync_api import sync_playwright, expect
import json
import time

def test_editor_dirty_state():
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
        initial_content = "key: value"
        def handle_config(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"content": initial_content})
            )

        page.route("**/cases", handle_cases)
        page.route("**/config?*", handle_config)

        # Navigate to the frontend
        print("Navigating to frontend...")
        page.goto("http://localhost:5173")

        # Wait for cases to load
        page.wait_for_selector("text=case-1")
        page.click("text=case-1")

        # Wait for ConfigEditor
        page.wait_for_selector("textarea")

        # Initial state: Not dirty, button says "Save"
        print("Checking initial state...")
        # Debug: print all buttons
        for btn in page.get_by_role("button").all():
             print(f"Button: '{btn.inner_text()}'")

        # Use partial text match and explicit exclusion of "Save*"
        save_btn = page.get_by_role("button", name="Save", exact=False).filter(has_text="Ctrl+S")
        expect(save_btn).to_be_visible()

        # Ensure it doesn't say "Save*"
        # inner_text should not contain "Save*"
        text = save_btn.inner_text()
        if "Save*" in text:
             raise AssertionError(f"Button contains 'Save*' but shouldn't: {text}")

        # Type a character
        print("Typing '!'...")
        page.focus("textarea")
        page.keyboard.type("!")

        # Wait for debounce (300ms) + buffer
        time.sleep(0.5)

        # Expect "Save*"
        print("Checking dirty state (Save*)...")
        save_dirty_btn = page.get_by_role("button", name="Save*", exact=False)
        expect(save_dirty_btn).to_be_visible()

        # Verify it has "Save*" explicitly
        text_dirty = save_dirty_btn.inner_text()
        if "Save*" not in text_dirty:
             raise AssertionError(f"Button should contain 'Save*': {text_dirty}")

        # Screenshot the dirty state
        print("Taking screenshot of dirty state...")
        page.screenshot(path="verification/dirty_state.png")

        # Revert change (Backspace)
        print("Reverting change (Backspace)...")
        page.keyboard.press("Backspace")

        # Wait for debounce
        time.sleep(0.5)

        # Expect "Save" (clean state)
        print("Checking clean state (Save)...")
        save_clean_btn = page.get_by_role("button", name="Save", exact=False).filter(has_text="Ctrl+S")
        expect(save_clean_btn).to_be_visible()

        text_clean = save_clean_btn.inner_text()
        if "Save*" in text_clean:
             raise AssertionError(f"Button should NOT contain 'Save*': {text_clean}")

        print("SUCCESS: Dirty state logic verified.")
        browser.close()

if __name__ == "__main__":
    test_editor_dirty_state()
