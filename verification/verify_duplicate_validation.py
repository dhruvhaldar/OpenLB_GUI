import time
import json
import re
from playwright.sync_api import sync_playwright

def verify_duplicate_validation():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Mock APIs
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([{
                "id": "case1",
                "path": "/cases/case1",
                "name": "case1",
                "domain": "Default"
            }])
        ))

        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"content": "<xml/>"})
        ))

        # Navigate to app
        try:
            page.goto("http://localhost:4173")
        except Exception:
             print("Could not connect to localhost:4173. Make sure 'pnpm preview' is running.")
             return

        # Select case
        page.get_by_text("case1").click()

        # Open Duplicate Modal
        page.get_by_role("button", name="Duplicate Case").click()

        # Helper to check state
        def check_state(name_input, expect_error, error_text_part=None):
            submit_btn = page.get_by_role("button", name="Duplicate", exact=True)
            is_disabled = submit_btn.is_disabled()

            error_msg = page.locator("#duplicate-error-msg")
            is_error_visible = error_msg.is_visible()

            if expect_error:
                if not is_disabled:
                    return False, "Submit button should be disabled"
                if not is_error_visible:
                    return False, "Error message should be visible"
                if error_text_part:
                    text = error_msg.text_content()
                    if error_text_part not in text:
                        return False, f"Error message '{text}' does not contain '{error_text_part}'"
            else:
                if is_disabled:
                    # Check if it's disabled because of empty input (handled separately)
                    if name_input and name_input.strip():
                         return False, "Submit button should be enabled"
                if is_error_visible:
                    return False, f"Error message should not be visible, got: {error_msg.text_content()}"

            return True, "OK"

        input_field = page.get_by_label("New Case Name")

        print("Testing Invalid Characters...")
        input_field.fill("bad/name")
        success, msg = check_state("bad/name", True, "alphanumeric")
        if not success:
            print(f"FAILED (Invalid Char): {msg}")
            browser.close()
            return

        print("Testing Reserved Name...")
        input_field.fill("COM1")
        success, msg = check_state("COM1", True, "reserved")
        if not success:
            print(f"FAILED (Reserved Name): {msg}")
            browser.close()
            return

        print("Testing Valid Name...")
        input_field.fill("good_name-123")
        success, msg = check_state("good_name-123", False)
        if not success:
            print(f"FAILED (Valid Name): {msg}")
            browser.close()
            return

        print("SUCCESS: Duplicate validation logic verified.")
        browser.close()

if __name__ == "__main__":
    verify_duplicate_validation()
