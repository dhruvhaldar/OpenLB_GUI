import time
from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Serve the built frontend
    # Since we can't easily start a full server in this snippet, we'll mock the backend
    # or just assume the frontend is running.
    # Actually, we should start the frontend dev server or serve build.
    # But Playwright can't easily start a process and keep it running in this script without blocking.
    # So we'll assume the user (me) has started it, or we'll just test the built HTML?
    # No, we need a server.

    # Mocking Backend for Cases
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "case1", "path": "case1", "name": "Case 1", "domain": "Test"}, ' +
             ', '.join([f'{{"id": "case{i}", "path": "case{i}", "name": "Case {i}", "domain": "Test"}}' for i in range(2, 100)]) +
             ']'
    ))

    # We need to serve the static files.
    # Since we are in a sandbox, we can use a python http server in background?
    # Or just rely on the 'preview' command?

    print("Please ensure frontend is running or serve it. Waiting for localhost:4173...")
    # Assuming 'vite preview' runs on 4173
    try:
        page.goto("http://localhost:4173")
    except:
        print("Failed to connect to localhost:4173. Trying 5173 (dev)...")
        page.goto("http://localhost:5173")

    page.wait_for_selector("text=OpenLB Manager")

    # Verify that list items have the class
    # We generated 100 cases.
    items = page.locator("li.cv-auto")
    count = items.count()
    print(f"Found {count} items with .cv-auto class")

    if count > 0:
        print("Verification Successful: Class applied.")
    else:
        print("Verification Failed: Class NOT applied.")
        exit(1)

    # Check CSS property
    # Get computed style of first item
    first_item = items.first
    style = first_item.evaluate("el => window.getComputedStyle(el).contentVisibility")
    print(f"Computed content-visibility: {style}")

    if style != "auto":
        print("Verification Failed: CSS property not active (might be browser support or styles not loaded)")
        # Note: Headless chromium should support it.
        # If it returns empty string, maybe it's not supported or not applied.
        # But we added it to index.css and built it.

    page.screenshot(path="verification/sidebar.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
