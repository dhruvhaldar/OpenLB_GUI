import time
from playwright.sync_api import sync_playwright, expect

def run(playwright):
    browser = playwright.chromium.launch(headless=True)
    page = browser.new_page()

    # Mock the API to return a sample case
    def handle_cases(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "ux-test-case", "domain": "tests", "path": "/tmp/ux-test-case"}]'
        )

    def handle_config(route):
        route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": "config content"}'
        )

    # Intercept API calls
    page.route("**/cases", handle_cases)
    page.route("**/config**", handle_config)

    print("Navigating to app...")
    page.goto("http://localhost:5173")

    # 1. Verify initial title
    print("Verifying initial title...")
    expect(page).to_have_title("OpenLB Manager")
    print("SUCCESS: Initial title is correct.")

    # 2. Click on the case
    print("Clicking on case 'ux-test-case'...")
    # Wait for the case to appear
    case_button = page.get_by_text("ux-test-case")
    case_button.click()

    # 3. Verify title change
    print("Verifying title after selection...")
    expect(page).to_have_title("ux-test-case - OpenLB Manager")
    print("SUCCESS: Title updated correctly.")

    # Take screenshot
    page.screenshot(path="verification/title_verification.png")
    print("Screenshot saved to verification/title_verification.png")

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
