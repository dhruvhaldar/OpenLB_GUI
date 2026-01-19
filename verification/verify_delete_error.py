import time
from playwright.sync_api import sync_playwright, expect

def verify_delete_error():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Mock the backend responses
        # 1. Cases list
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "test-case", "path": "/path/to/test-case", "domain": "test-domain"}]'
        ))

        # 2. Config
        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": "dummy config"}'
        ))

        # 3. Delete case - simulate error
        page.route("**/cases?case_path=*", lambda route: route.fulfill(
            status=400,
            content_type="application/json",
            body='{"detail": "Cannot delete case because it is locked by another process."}'
        ))

        # Go to app
        page.goto("http://localhost:5173")

        # Wait for cases to load
        page.wait_for_selector("text=test-case")

        # Select case
        page.click("text=test-case")

        # Wait for case details to load
        page.wait_for_selector("text=test-domain / test-case")

        # Click delete button in header
        # The delete button has a trash icon and title "Delete Case"
        delete_btn = page.get_by_label("Delete Case")
        delete_btn.click()

        # Check modal is open
        # We target the one with "Delete Case" text to differentiate from Duplicate modal
        dialog = page.locator("dialog").filter(has_text="Delete Case")
        expect(dialog).to_be_visible()

        # Click Delete in modal
        modal_delete_btn = dialog.locator("button", has_text="Delete")
        modal_delete_btn.click()

        # Check for error message
        # We added role="alert" to the error message
        error_msg = page.get_by_role("alert")
        expect(error_msg).to_be_visible()
        expect(error_msg).to_have_text("Cannot delete case because it is locked by another process.")

        # Take screenshot
        page.screenshot(path="verification/delete_error_modal.png")
        print("Screenshot saved to verification/delete_error_modal.png")

        browser.close()

if __name__ == "__main__":
    verify_delete_error()
