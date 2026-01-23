
from playwright.sync_api import Page, expect, sync_playwright

def verify_save_hint(page: Page):
    # 1. Arrange: Go to the app
    # Wait for the server to be ready
    try:
        page.goto("http://localhost:5173", timeout=10000)
    except Exception as e:
        print(f"Failed to load page: {e}")
        raise

    # Mock backend to return a case so we see the main content
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "1", "name": "test-case", "domain": "cylinder-flow", "path": "/tmp/test-case", "config": ""}]'
    ))

    # Also mock config fetch
    page.route("**/config?path=*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"content": "simulation_config"}'
    ))

    # Wait for the case to load and be selectable
    page.reload()

    # Wait for the sidebar to load cases
    page.wait_for_selector("text=test-case")

    # Click the case to select it
    page.click("text=test-case")

    # 2. Act: Wait for the Config Editor to load
    # Look for the Save button
    # The ConfigEditor header contains the Save button

    save_btn = page.locator("button:has-text('Save')").first
    expect(save_btn).to_be_visible()

    # 3. Assert: Check if the shortcut hint is visible
    # We look for the text "Ctrl+S"
    expect(save_btn).to_contain_text("Ctrl+S")

    # Check if the kbd element exists inside
    kbd = save_btn.locator("kbd")
    expect(kbd).to_be_visible()

    # Check classes of kbd to ensure it has the styling we added
    expect(kbd).to_have_class(re.compile(r"hidden md:inline-block"))
    expect(kbd).to_have_class(re.compile(r"bg-black/20"))

    print("Verification passed: Save button contains Ctrl+S hint.")

    # 4. Screenshot
    page.screenshot(path="verification/save_hint.png")
    print("Screenshot saved to verification/save_hint.png")

if __name__ == "__main__":
    import re
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_save_hint(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error_save_hint.png")
            raise
        finally:
            browser.close()
