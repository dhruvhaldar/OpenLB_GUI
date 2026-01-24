import os
from playwright.sync_api import sync_playwright, expect

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock API responses
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "test-case", "domain": "cylinder", "path": "/path/to/test-case"}]'
        ))
        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": "config content"}'
        ))

        page.goto("http://localhost:5173")

        # Wait for sidebar to load and click the case
        page.get_by_role("button", name="test-case").click()

        # Wait for header to appear (Check for Duplicate button)
        duplicate_btn = page.get_by_role("button", name="Duplicate Case")
        expect(duplicate_btn).to_be_visible()
        duplicate_btn.click()

        # Wait for modal - Now checking by Role and Name!
        # This confirms that aria-labelledby is working because <dialog> does not have aria-label.
        # It relies on the labelledby relationship to get its accessible name from the title.
        dialog = page.get_by_role("dialog", name="Duplicate Case")
        expect(dialog).to_be_visible()

        # Double check aria-labelledby attribute presence just to be sure
        aria_labelledby = dialog.get_attribute("aria-labelledby")
        if not aria_labelledby:
            raise Exception("Dialog is missing aria-labelledby attribute")

        print(f"Found aria-labelledby: {aria_labelledby}")

        # Verify the title has this ID
        title_el = page.locator(f"#{aria_labelledby}")
        expect(title_el).to_be_visible()
        expect(title_el).to_have_text("Duplicate Case")

        print("Verified title element exists and has correct text.")

        # Take screenshot
        os.makedirs("verification", exist_ok=True)
        page.screenshot(path="verification/modal_a11y.png")
        print("Screenshot saved.")

        browser.close()

if __name__ == "__main__":
    run()
