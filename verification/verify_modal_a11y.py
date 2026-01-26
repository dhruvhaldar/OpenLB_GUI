import time
from playwright.sync_api import sync_playwright

def test_modal_accessibility(page):
    print("Navigating to http://localhost:5173")
    page.goto("http://localhost:5173")

    # Mock API to provide a case so we can open the duplicate modal
    print("Mocking API responses...")
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

    # Reload to apply mocked data
    print("Reloading page...")
    page.reload()

    # Click on the case in sidebar to select it
    print("Selecting 'Case1'...")
    page.get_by_text("Case1").click()

    # Click Duplicate button
    # Use get_by_role to distinguish from the dialog which also has the name "Duplicate Case"
    print("Clicking Duplicate button...")
    page.get_by_role("button", name="Duplicate Case").click()

    # Wait for modal to be visible
    print("Waiting for modal...")
    modal = page.locator("dialog").first
    modal.wait_for(state="visible")

    # Check aria-labelledby
    aria_labelled_by = modal.get_attribute("aria-labelledby")
    print(f"Found aria-labelledby: {aria_labelled_by}")

    if not aria_labelled_by:
        print("FAIL: Modal missing aria-labelledby attribute")
        return False

    # Check if the label element exists
    title_element = page.locator(f"#{aria_labelled_by}")
    if title_element.count() == 0:
        print(f"FAIL: Element with id '{aria_labelled_by}' not found")
        return False

    # Check text match
    title_text = title_element.inner_text()
    if title_text != "Duplicate Case":
        print(f"FAIL: Label text mismatch. Expected 'Duplicate Case', got '{title_text}'")
        return False

    print("SUCCESS: Modal has correct aria-labelledby")

    # Take screenshot
    page.screenshot(path="verification/verification.png")
    print("Screenshot saved to verification/verification.png")

    return True

if __name__ == "__main__":
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            success = test_modal_accessibility(page)
            if not success:
                exit(1)
        except Exception as e:
            print(f"Error: {e}")
            exit(1)
        finally:
            browser.close()
