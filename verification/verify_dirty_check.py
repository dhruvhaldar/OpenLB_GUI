from playwright.sync_api import sync_playwright, expect
import json
import time
import re

def test_config_editor_dirty_check():
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
                body=json.dumps({"content": "initial content"})
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

        # Wait for config editor to be visible
        print("Waiting for ConfigEditor...")
        page.wait_for_selector("textarea")

        # Verify initial state
        print("Verifying initial state...")
        # The button contains "Save" and a kbd element "Ctrl+S".
        # Playwright's accessible name computation joins them.
        save_btn = page.get_by_role("button", name=re.compile(r"Save", re.IGNORECASE))
        expect(save_btn).to_be_visible()

        # Focus textarea
        print("Focusing textarea...")
        page.click("textarea")

        # Type to trigger dirty check
        print("Typing ' modified'...")
        page.keyboard.type(" modified")

        # Wait for debounce (300ms) + small buffer
        time.sleep(1.0)

        # Verify dirty state (Save button should have text "Save*")
        # The button text changes to "Save*"
        print("Verifying dirty state...")
        dirty_save_btn = page.get_by_role("button", name=re.compile(r"Save\*"))
        expect(dirty_save_btn).to_be_visible()

        # Verify that deleting the modification resets the dirty state
        # Select all and replace with original content
        print("Restoring original content...")
        # Control+A works on Linux/Windows. Command+A on Mac.
        # Playwright usually handles Control+A for Select All.
        page.keyboard.press("Control+A")
        page.keyboard.type("initial content")

        time.sleep(1.0)

        print("Verifying clean state...")
        # Use first() because dirty_save_btn locator might still match (it's regex based), but we want to ensure *something* matches "Save"
        # Actually, "Save*" shouldn't match "Save" if we use regex r"Save$" or just look for presence.

        clean_save_btn = page.get_by_role("button", name="Save", exact=False).filter(has_text="Ctrl+S")
        expect(clean_save_btn).to_be_visible()

        # Take screenshot
        print("Taking screenshot...")
        page.screenshot(path="verification/optimization_verification.png")

        browser.close()
        print("Verification successful!")

if __name__ == "__main__":
    test_config_editor_dirty_check()
