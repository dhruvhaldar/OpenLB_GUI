import time
import json
from playwright.sync_api import sync_playwright

def verify_ux_screenshot():
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

        # Navigate
        try:
             page.goto("http://localhost:4173")
        except Exception:
             print("Server not running?")
             return

        # Select case and open modal
        page.get_by_text("case1").click()
        page.get_by_role("button", name="Duplicate Case").click()

        # Type invalid name to trigger error
        input_field = page.get_by_label("New Case Name")
        input_field.fill("bad/name")

        # Wait for error
        page.locator("#duplicate-error-msg").wait_for()

        # Take screenshot
        page.screenshot(path="verification/duplicate_validation_error.png")
        print("Screenshot saved to verification/duplicate_validation_error.png")

        browser.close()

if __name__ == "__main__":
    verify_ux_screenshot()
