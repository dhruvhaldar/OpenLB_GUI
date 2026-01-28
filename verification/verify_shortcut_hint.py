from playwright.sync_api import Page, expect, sync_playwright

def verify_shortcut_hint(page: Page):
    # Mock the cases endpoint to ensure we have cases but none selected
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "1", "name": "simulation1", "domain": "example", "path": "/tmp/sim1"}]'
    ))

    # Go to the app
    page.goto("http://localhost:5173")

    # Wait for the sidebar to show the case
    expect(page.get_by_text("simulation1")).to_be_visible()

    # Verify the "No Case Selected" header is visible
    expect(page.get_by_role("heading", name="No Case Selected")).to_be_visible()

    # Verify the new hint text
    expect(page.get_by_text("Press")).to_be_visible()
    expect(page.get_by_text("/")).to_be_visible()
    expect(page.get_by_text("to search cases")).to_be_visible()

    # Take a screenshot
    page.screenshot(path="verification/shortcut_hint.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_shortcut_hint(page)
        finally:
            browser.close()
