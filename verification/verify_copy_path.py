
import re
import json
from playwright.sync_api import sync_playwright, expect

def verify_copy_path():
    with sync_playwright() as p:
        # Launch browser with clipboard permissions
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        context.grant_permissions(['clipboard-read', 'clipboard-write'])

        page = context.new_page()

        # Mock the cases endpoint to return a dummy case
        cases_data = [
            {
                "id": "case1",
                "name": "cylinder2d",
                "domain": "examples/laminar",
                "path": "/home/user/olb/examples/laminar/cylinder2d"
            }
        ]

        # Mock config endpoint to avoid errors
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            body=json.dumps(cases_data),
            headers={"Content-Type": "application/json"}
        ))

        page.route(re.compile(r".*/config\?path=.*"), lambda route: route.fulfill(
            status=200,
            body=json.dumps({"content": "SimConfig content..."}),
            headers={"Content-Type": "application/json"}
        ))

        # Navigate to the app
        page.goto("http://localhost:5173")

        # Wait for the case to appear in the sidebar
        sidebar_item = page.get_by_text("cylinder2d")
        expect(sidebar_item).to_be_visible()

        # Click the case to select it
        sidebar_item.click()

        # Verify the header is visible
        header = page.get_by_role("heading", name="examples/laminar / cylinder2d")
        expect(header).to_be_visible()

        # Find the copy button
        # It's an icon-only button with aria-label "Copy case path"
        copy_button = page.get_by_role("button", name="Copy case path")
        expect(copy_button).to_be_visible()

        # Take a screenshot before interaction
        page.screenshot(path="/home/jules/verification/before_click.png")

        # Click the copy button
        copy_button.click()

        # Verify the button changes state (Check icon)
        # The aria-label should change to "Copied path"
        # And title to "Copied!"
        copied_button = page.get_by_role("button", name="Copied path")
        expect(copied_button).to_be_visible()

        # Verify clipboard content
        clipboard_text = page.evaluate("navigator.clipboard.readText()")
        assert clipboard_text == "/home/user/olb/examples/laminar/cylinder2d", f"Clipboard content mismatch: {clipboard_text}"

        # Take a screenshot of the success state
        page.screenshot(path="/home/jules/verification/after_click.png")

        print("Verification successful!")
        browser.close()

if __name__ == "__main__":
    verify_copy_path()
