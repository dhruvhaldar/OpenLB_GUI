import time
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock the API to simulate loading.
    # We intentionally do not fulfill the request to keep the app in loading state.
    def handle_route(route):
        # Just pass, effectively hanging the request
        pass

    # Intercept the specific call to /cases
    page.route("**/cases", handle_route)

    print("Navigating to app...")
    page.goto("http://localhost:5173")

    # Verify the loading state
    print("Waiting for 'Loading Cases...' text...")
    loading_text = page.get_by_text("Loading Cases...")

    try:
        expect(loading_text).to_be_visible(timeout=5000)
        print("SUCCESS: Loading state is visible.")
    except Exception as e:
        print(f"FAILURE: Loading state not found. {e}")
        page.screenshot(path="verification/failure_debug.png")
        browser.close()
        raise e

    # Take screenshot
    page.screenshot(path="verification/loading_state.png")
    print("Screenshot saved to verification/loading_state.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
