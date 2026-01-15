from playwright.sync_api import sync_playwright, expect

def verify_word_wrap():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the preview server
        page.goto("http://localhost:4173")

        # Mock backend responses to enable UI interaction
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "test_case", "domain": "cylinder", "path": "cases/cylinder/test_case"}]'
        ))

        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": "simulation_config { ... }"}'
        ))

        # Select the case
        page.get_by_role("button", name="test_case").click()

        # Inject long log output to test wrapping
        long_line = "A" * 200 # Long string without spaces

        # We can't easily inject state into React from outside without a backdoor,
        # but we can rely on the UI being present.
        # Since we can't easily trigger a run that produces output without a real backend,
        # we might need to rely on the fact that the button exists and toggles the class.
        # Wait, the LogViewer shows "No output generated yet" initially.

        # Let's verify the button exists and has the correct initial state.
        wrap_button = page.get_by_role("button", name="Enable word wrap")
        expect(wrap_button).to_be_visible()

        # Take screenshot of initial state
        page.screenshot(path="verification/before_toggle.png")

        # Click the button
        wrap_button.click()

        # Verify state change
        expect(page.get_by_role("button", name="Disable word wrap")).to_be_visible()

        # Take screenshot of toggled state
        page.screenshot(path="verification/after_toggle.png")

        browser.close()

if __name__ == "__main__":
    verify_word_wrap()
