from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock backend response for cases to be empty
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body="[]"
    ))

    # Mock other requests to avoid 404s
    page.route("**/config**", lambda route: route.fulfill(status=200, body='{"content": ""}'))

    try:
        page.goto("http://localhost:5173", timeout=10000)

        # Wait for loading to finish and empty state to appear
        # The loading state text is "Loading cases..."
        # The empty state text is "No Simulation Cases Found"

        # Wait for the specific empty state element
        page.get_by_text("No Simulation Cases Found").wait_for(timeout=5000)

        # Take screenshot
        page.screenshot(path="verification/empty_state.png")
        print("Screenshot taken.")

    except Exception as e:
        print(f"Error: {e}")
        page.screenshot(path="verification/error.png")
    finally:
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run(playwright)
