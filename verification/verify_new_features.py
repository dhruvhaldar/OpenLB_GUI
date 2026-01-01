import re
from playwright.sync_api import sync_playwright, expect

def verify_features(page):
    # Mock backend responses
    # 1. Mock list cases (initial load)
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "Aerospace/cyl_flow", "path": "/abs/path/Aerospace/cyl_flow", "name": "cyl_flow", "domain": "Aerospace"}]'
    ))

    # 2. Mock config (when case selected)
    page.route("**/config?path=*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"content": "<xml>config</xml>"}'
    ))

    # 3. Mock Duplicate
    page.route("**/cases/duplicate", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"success": true, "new_path": "/abs/path/Aerospace/cyl_flow_copy"}'
    ))

    # 4. Mock Delete
    page.route("**/cases?case_path=*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"success": true}'
    ))

    # Load app
    page.goto("http://localhost:5173")

    # Wait for cases to load
    page.get_by_text("cyl_flow").click()

    # 1. Verify Download Button Exists (Output section)
    # It might be hidden if no output, but the button should be there in the header
    expect(page.get_by_role("button", name="Download output")).to_be_visible()

    # 2. Click Duplicate
    # We need to mock window.prompt
    page.on("dialog", lambda dialog: dialog.accept("cyl_flow_copy"))
    page.get_by_role("button", name="Duplicate Case").click()

    # In a real app, this would refresh the list. Since we mocked the duplicate call
    # but not the subsequent list refresh (which happens inside handleDuplicate),
    # we should handle the second /cases call if we want to see the new item.
    # But for visual verification of buttons, seeing the button is enough.

    # 3. Verify Delete Button Exists
    expect(page.get_by_role("button", name="Delete Case")).to_be_visible()

    # Take screenshot of the header area and output area
    page.screenshot(path="verification/screenshots/features.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            verify_features(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/screenshots/error.png")
            raise
        finally:
            browser.close()
