
import re
from playwright.sync_api import Page, expect, sync_playwright

def verify_shortcuts(page: Page):
    # 1. Arrange: Go to the app
    page.goto("http://localhost:5173")

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

    # 2. Act: Wait for the Build and Run buttons to be visible
    # There might be duplicate buttons in the empty state, so we target the header buttons
    # The header is inside <header> tag
    header = page.locator("header")

    build_btn = header.locator("button:has-text('Build')")
    run_btn = header.locator("button:has-text('Run')")

    expect(build_btn).to_be_visible()
    expect(run_btn).to_be_visible()

    # 3. Assert: Check if the shortcuts are visible
    # We look for the text "Ctrl+B" and "Ctrl+Enter"
    expect(build_btn).to_contain_text("Ctrl+B")
    expect(run_btn).to_contain_text("Ctrl+Enter")

    # Check if the kbd element exists inside
    expect(build_btn.locator("kbd")).to_be_visible()
    expect(run_btn.locator("kbd")).to_be_visible()

    # 4. Screenshot
    page.screenshot(path="verification/shortcuts.png")
    print("Screenshot saved to verification/shortcuts.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_shortcuts(page)
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="verification/error.png")
        finally:
            browser.close()
