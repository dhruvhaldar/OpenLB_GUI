import json
from playwright.sync_api import sync_playwright, expect

def test_duplicate_modal(page):
    # Mock the API responses
    page.route("**/cases", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps([
            {"id": "1", "name": "base-case", "path": "cases/base-case", "domain": "cylinder"}
        ])
    ))

    # Mock config fetch
    page.route("**/config?path=*", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"content": "simulation config..."})
    ))

    # Mock duplicate endpoint
    page.route("**/cases/duplicate", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"new_path": "cases/base-case_copy"})
    ))

    # Visit the app
    # Assuming the app is running on localhost:5173
    page.goto("http://localhost:5173")

    # Wait for cases to load
    page.get_by_role("button", name="base-case").click()

    # Click duplicate button
    # The button has aria-label="Duplicate Case"
    page.get_by_role("button", name="Duplicate Case").click()

    # Verify modal is visible
    modal = page.get_by_role("dialog")
    expect(modal).to_be_visible()

    # Verify input is focused and pre-filled
    input_field = page.get_by_label("New Case Name")
    expect(input_field).to_be_visible()
    expect(input_field).to_have_value("base-case_copy")
    expect(input_field).to_be_focused()

    # Take screenshot of the modal
    page.screenshot(path="/home/jules/verification/duplicate_modal_open.png")

    # Fill new name
    input_field.fill("new-cool-case")

    # Submit
    page.get_by_role("button", name="Duplicate", exact=True).click()

    # Verify modal closes (after mock success)
    # Note: Our mock doesn't update the cases list with the new case, but the success logic closes the modal.
    # In the app logic:
    # 1. API call returns success
    # 2. Refreshes cases (mocked to return same list, so new case won't be found)
    # 3. Sets modal open to false.

    expect(modal).not_to_be_visible()

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_duplicate_modal(page)
            print("Verification script finished successfully.")
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/failure.png")
            raise
        finally:
            browser.close()
