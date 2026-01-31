import os
import time
from playwright.sync_api import sync_playwright, expect

def test_editor_dirty_check():
    print("Starting verification...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to app
        try:
            page.goto("http://localhost:5173", timeout=10000)
        except Exception as e:
            print(f"Failed to load page: {e}")
            return

        # Wait for cases to load
        print("Waiting for cases...")
        try:
            # Look for a button with text "cyl_flow"
            # It might be in "Uncategorized" section.
            case_btn = page.get_by_role("button", name="cyl_flow").first
            case_btn.wait_for(state="visible", timeout=10000)
            case_btn.click()
            print("Selected case 'cyl_flow'.")
        except Exception as e:
            print(f"Failed to select case: {e}")
            page.screenshot(path="verification_screenshots/failed_selection.png")
            return

        # Wait for config editor to load
        print("Waiting for config editor...")
        try:
            expect(page.get_by_text("Configuration")).to_be_visible(timeout=5000)

            # Find textarea
            textarea = page.locator("textarea")
            expect(textarea).to_be_visible()

            # Get initial value
            initial_value = textarea.input_value()
            print(f"Initial config length: {len(initial_value)}")

            # Type a character to trigger dirty state
            # We append a space
            textarea.type(" ")

            # Check if Save button becomes "Save*" (dirty)
            # From code: isDirty ? 'Save*' : 'Save'
            save_btn = page.get_by_role("button", name="Save*")
            expect(save_btn).to_be_visible(timeout=2000)
            print("Save button marked dirty (optimization works functionally).")

            # Take screenshot
            os.makedirs("verification_screenshots", exist_ok=True)
            page.screenshot(path="verification_screenshots/editor_dirty.png")
            print("Screenshot saved to verification_screenshots/editor_dirty.png")

        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="verification_screenshots/failed_editor.png")

        browser.close()

if __name__ == "__main__":
    test_editor_dirty_check()
