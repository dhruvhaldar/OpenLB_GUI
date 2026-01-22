import time
from playwright.sync_api import sync_playwright

def test_sidebar_navigation():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Create a context with mock API routes
        context = browser.new_context()
        page = context.new_page()

        # Mock API responses
        # Cases list
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id":"1","name":"Case A","domain":"Test","path":"/path/to/caseA"},{"id":"2","name":"Case B","domain":"Test","path":"/path/to/caseB"},{"id":"3","name":"Case C","domain":"Test","path":"/path/to/caseC"}]'
        ))

        # Config for selected case
        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content":"simulation config content"}'
        ))

        # Navigate to the app
        # Wait for the server to be ready
        max_retries = 10
        for i in range(max_retries):
            try:
                page.goto("http://localhost:5173")
                break
            except Exception:
                if i == max_retries - 1:
                    raise
                time.sleep(1)

        # Wait for cases to load
        page.wait_for_selector("text=Case A")

        # Focus the list (simulate user interaction)
        # Since we can't easily tab to it without multiple tabs, we'll click the first item to give focus context,
        # then test keyboard navigation.

        # Click first item
        page.click("text=Case A")

        # Verify it is selected (blue background)
        case_a = page.locator("button:has-text('Case A')")

        # In our implementation, clicking selects it.
        # Now press ArrowDown
        page.keyboard.press("ArrowDown")

        # Verify Case B is focused
        case_b = page.locator("button:has-text('Case B')")
        # Check if focused
        if not case_b.evaluate("el => el === document.activeElement"):
             print("Case B is NOT focused after ArrowDown")
        else:
             print("Case B IS focused after ArrowDown")

        # Press ArrowDown again
        page.keyboard.press("ArrowDown")

        # Verify Case C is focused
        case_c = page.locator("button:has-text('Case C')")
        if not case_c.evaluate("el => el === document.activeElement"):
             print("Case C is NOT focused after ArrowDown")
        else:
             print("Case C IS focused after ArrowDown")

        # Press ArrowUp
        page.keyboard.press("ArrowUp")
        if not case_b.evaluate("el => el === document.activeElement"):
             print("Case B is NOT focused after ArrowUp")
        else:
             print("Case B IS focused after ArrowUp")

        # Take screenshot of the state
        page.screenshot(path="verification/sidebar_nav.png")
        print("Screenshot saved to verification/sidebar_nav.png")

        browser.close()

if __name__ == "__main__":
    test_sidebar_navigation()
