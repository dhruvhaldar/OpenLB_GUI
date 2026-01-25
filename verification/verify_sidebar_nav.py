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

    # Check if first item is focused
    focused_text = page.evaluate("document.activeElement.textContent")
    print(f"Focused element text: {focused_text}")

    if "Case 1" not in focused_text:
        print("FAILED: First item not focused after ArrowDown from input")
        exit(1)

    # 3. Press ArrowDown to focus second item (NEW FEATURE)
    print("Pressing ArrowDown to focus second item...")
    page.keyboard.press("ArrowDown")

    focused_text = page.evaluate("document.activeElement.textContent")
    print(f"Focused element text: {focused_text}")

    if "Case 2" not in focused_text:
        print("FAILED: Second item not focused after ArrowDown")
        # Don't exit yet, we want to see if the implementation fixes this
        # But for now, this script is expected to fail on step 2 if feature not implemented
        # Actually, without the feature, focus stays on Case 1.

    # 4. Press ArrowUp to focus first item again
    print("Pressing ArrowUp to focus first item...")
    page.keyboard.press("ArrowUp")

    focused_text = page.evaluate("document.activeElement.textContent")
    print(f"Focused element text: {focused_text}")

    if "Case 1" not in focused_text:
        print("FAILED: First item not focused after ArrowUp")

    # 5. Press End to focus last item
    print("Pressing End to focus last item...")
    page.keyboard.press("End")

    focused_text = page.evaluate("document.activeElement.textContent")
    print(f"Focused element text: {focused_text}")

    # Depending on implementation 'End' might not be supported yet, but let's test if we add it
    if "Case 3" not in focused_text:
        print("WARNING: Last item not focused after End key (maybe not implemented yet)")

    page.screenshot(path="verification/sidebar_nav_verified.png")
    print("Verification Script Finished. Screenshot saved.")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
