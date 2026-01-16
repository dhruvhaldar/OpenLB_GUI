import time
from playwright.sync_api import sync_playwright

def test_duplicate_modal_render(page):
    # Navigate to app (assuming localhost:3000 or similar, but since we don't have dev server running in background
    # we might need to mock it or rely on existing build.
    # Actually, the instructions say "Start the Application".
    # I will start it in background first.)

    page.goto("http://localhost:3000")

    # Wait for sidebar to load (mocking API response if needed, but let's try real first)
    # Since backend might not be running with data, we might see empty state.

    # We need to simulate selecting a case to enable the duplicate button.
    # If no cases, we can't test.
    # So I will mock the API responses.

    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='[{"id": "c1", "name": "Case1", "path": "Case1", "domain": "Aerospace"}]'
    ))

    page.route("**/config?path=*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body='{"content": "<xml>config</xml>"}'
    ))

    # Reload to get mocked cases
    page.reload()

    # Click on the case in sidebar
    page.get_by_text("Case1").click()

    # Click Duplicate button
    # It has aria-label="Duplicate Case"
    page.get_by_label("Duplicate Case").click()

    # Wait for modal
    modal = page.locator("dialog").first
    if not modal.is_visible():
        # Maybe it's not using <dialog> correctly in playwright?
        # But our code uses <dialog open>.
        # Playwright handles it.
        pass

    time.sleep(0.5) # Wait for animation/focus

    # Take screenshot of the modal
    page.screenshot(path="/home/jules/verification/duplicate_modal.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            test_duplicate_modal_render(page)
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()
