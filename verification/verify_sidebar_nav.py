import time
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mocking Backend for Cases
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "case1", "path": "case1", "name": "Case 1", "domain": "Test"}, ' +
             '{"id": "case2", "path": "case2", "name": "Case 2", "domain": "Test"}, ' +
             '{"id": "case3", "path": "case3", "name": "Case 3", "domain": "Test"}]'
    ))

    print("Connecting to frontend...")
    try:
        page.goto("http://localhost:4173")
    except:
        print("Failed to connect to localhost:4173. Trying 5173 (dev)...")
        page.goto("http://localhost:5173")

    page.wait_for_selector("text=OpenLB Manager")

    # Wait for cases to load
    page.wait_for_selector("text=Case 1")

    # 1. Focus Search Input
    print("Focusing search input...")
    page.click("input[placeholder*='Filter cases']")

    # 2. Press ArrowDown to focus first item (Existing feature)
    print("Pressing ArrowDown to focus first item...")
    page.keyboard.press("ArrowDown")

    # VERIFY STEP 2 (Restored)
    focused_text = page.evaluate("document.activeElement.textContent")
    if "Case 1" not in focused_text:
        print(f"FAILED: First item not focused after ArrowDown from input. Focused: {focused_text}")
        exit(1)
    print("SUCCESS: Focused first item.")

    # 3. Press ArrowDown to focus second item (NEW FEATURE)
    print("Pressing ArrowDown to focus second item...")
    page.keyboard.press("ArrowDown")

    # Take screenshot of Sidebar
    sidebar = page.locator("aside")
    sidebar.screenshot(path="verification/sidebar_focus.png")
    print("Screenshot saved to verification/sidebar_focus.png")

    focused_text = page.evaluate("document.activeElement.textContent")
    print(f"Focused element text: {focused_text}")

    if "Case 2" not in focused_text:
        print(f"FAILED: Second item not focused after ArrowDown. Focused: {focused_text}")
        exit(1)
    print("SUCCESS: Focused second item.")

    print("Verification Script Finished.")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
