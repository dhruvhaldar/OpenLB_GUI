from playwright.sync_api import sync_playwright, expect

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock the backend API
        # We use a wildcard for cases to match potential query params if any, but exact match is fine too
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "test_case", "path": "test_case", "domain": "cylinder"}]',
            headers={"Access-Control-Allow-Origin": "*"}
        ))

        page.route("**/config*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": "dummy config"}',
            headers={"Access-Control-Allow-Origin": "*"}
        ))

        print("Navigating to app...")
        page.goto("http://localhost:5173")

        # Select the case
        print("Selecting case...")
        page.get_by_role("button", name="test_case").click()

        # Wait for header
        print("Waiting for buttons...")
        # Note: The button text is "Build" inside the button.
        build_btn = page.get_by_role("button", name="Build", exact=True)
        run_btn = page.get_by_role("button", name="Run", exact=True)

        # Check titles
        print("Checking attributes...")
        # The title might be "Build simulation (Ctrl+B)" or "Run simulation (Ctrl+Enter)"
        # The exact text depends on status=idle, which is default.

        # We need to wait for the element to have the attribute, so we use expect
        expect(build_btn).to_have_attribute("title", "Build simulation (Ctrl+B)")
        expect(run_btn).to_have_attribute("title", "Run simulation (Ctrl+Enter)")

        # Hover to see if tooltip appears (might not show in screenshot but good for interaction)
        build_btn.hover()

        print("Taking screenshot...")
        page.screenshot(path="verification/verification.png")
        print("Verification successful!")

        browser.close()

if __name__ == "__main__":
    run()
