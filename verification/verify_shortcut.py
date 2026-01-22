import time
from playwright.sync_api import sync_playwright

def verify_save_shortcut_hint():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        # Mock API responses to render the UI
        # 1. Cases list
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "test-case", "domain": "cylinder", "path": "/path/to/case"}]'
        ))

        # 2. Config content
        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": "config content"}'
        ))

        # Navigate to the app
        page.goto("http://localhost:5173")

        # Wait for sidebar to load and click the case
        page.get_by_role("button", name="test-case").click()

        # Wait for ConfigEditor to load
        # It has a heading "Configuration"
        page.get_by_text("Configuration").wait_for()

        # Locate the Save button
        # It should contain "Save" and the new shortcut hint "Ctrl+S"
        save_btn = page.locator("button", has_text="Save")

        # Verify the button text content contains Ctrl+S
        # Note: textContent gets all text, including hidden ones if they are in DOM
        # The kbd is visible on desktop (md:inline-block)
        print(f"Button text: {save_btn.text_content()}")

        # Take a screenshot of the ConfigEditor header area
        # We can try to screenshot just the button or the whole editor
        page.screenshot(path="verification/config_editor_shortcut.png")

        browser.close()

if __name__ == "__main__":
    verify_save_shortcut_hint()
