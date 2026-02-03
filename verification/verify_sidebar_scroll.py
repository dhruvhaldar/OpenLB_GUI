from playwright.sync_api import sync_playwright, expect
import json
import time

def test_sidebar_scroll():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Initial cases
        cases = []
        for i in range(20):
            cases.append({
                "id": f"case-{i}",
                "path": f"/path/to/case-{i}",
                "name": f"case-{i}",
                "domain": "TestDomain"
            })

        # Sort cases by name (as backend does)
        cases.sort(key=lambda x: x["name"])

        def handle_cases(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(cases)
            )

        def handle_duplicate(route):
            # Add new case to list (sorted at end)
            new_case = {
                "id": "case-z-new",
                "path": "/path/to/case-z-new",
                "name": "z-new-case",
                "domain": "TestDomain"
            }
            # Update the cases list for subsequent fetches
            cases.append(new_case)
            cases.sort(key=lambda x: x["name"])

            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"case": new_case})
            )

        page.route("**/cases", handle_cases)
        page.route("**/cases/duplicate", handle_duplicate)
        page.route("**/config?*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({"content": "config content"})))

        print("Navigating to frontend...")
        page.goto("http://localhost:5173")

        # Wait for cases
        print("Waiting for cases...")
        page.wait_for_selector("text=case-0")

        # Select first case
        print("Selecting case-0...")
        page.click("text=case-0")

        # Check title
        print("Checking initial title...")
        time.sleep(0.5) # Allow title update
        title = page.title()
        print(f"Current title: {title}")

        # Click Duplicate button (CopyPlus icon)
        print("Clicking Duplicate...")
        # Use get_by_role to disambiguate from the modal dialog
        page.get_by_role("button", name="Duplicate Case").click()

        # Fill modal
        print("Filling duplicate form...")
        page.fill("input#caseName", "z-new-case")

        # Submit
        print("Submitting duplicate...")
        # Be specific about the button in the modal
        page.click("button[type='submit']:has-text('Duplicate')")

        # Wait for new case to appear in list
        print("Waiting for z-new-case...")
        new_case_loc = page.locator("button:has-text('z-new-case')")
        new_case_loc.wait_for()

        # Verify it is selected
        print("Verifying selection...")
        expect(new_case_loc).to_have_attribute("aria-current", "true")

        # Verify it is in viewport (should auto-scroll)
        print("Verifying visibility (auto-scroll)...")
        # We might need to wait a bit for scroll animation
        time.sleep(1)

        # Check if it is in viewport
        if new_case_loc.is_visible():
             print("PASS: Element is visible")
        else:
             print("FAIL: Element is not visible")

        # Verify new title
        print("Checking new title...")
        title = page.title()
        print(f"New title: {title}")
        if "z-new-case" in title:
             print("PASS: Title updated")
        else:
             print("FAIL: Title not updated (Expected 'z-new-case...')")

        page.screenshot(path="verification/verify_sidebar_scroll_result.png")
        browser.close()

if __name__ == "__main__":
    test_sidebar_scroll()
