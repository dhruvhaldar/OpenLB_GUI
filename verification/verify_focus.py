from playwright.sync_api import sync_playwright, expect
import json
import time
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cases = [
            {"id": "c1", "path": "/c1", "name": "case-1", "domain": "d1"},
            {"id": "c2", "path": "/c2", "name": "case-2", "domain": "d1"}
        ]

        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(cases)
        ))

        # Mock other calls
        page.route("**/config*", lambda r: r.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"content": "foo"})
        ))

        print("Navigating...")
        try:
            page.goto("http://localhost:4173")
        except Exception as e:
            print(f"Failed to navigate: {e}")
            return

        # Wait for cases
        try:
            page.wait_for_selector("text=case-1", timeout=5000)
        except:
            print("Timeout waiting for case-1")
            page.screenshot(path="verification/error.png")
            return

        # Click to select (which sets isSelected=true)
        page.click("text=case-1")

        # Verify selected state (bg-blue-600)
        item = page.locator("button[aria-current='true']")
        expect(item).to_be_visible()

        # Focus the item (Simulate keyboard navigation)
        item.focus()

        # Take screenshot of the sidebar
        sidebar = page.locator("aside")
        sidebar.screenshot(path="verification/focus_ring_sidebar.png")
        print("Screenshot saved to verification/focus_ring_sidebar.png")

        # Now check Run button
        # Run button is in header.
        run_btn = page.locator("header").get_by_role("button", name="Run")

        # Focus it
        run_btn.focus()

        # Take screenshot of header
        header = page.locator("header")
        header.screenshot(path="verification/focus_ring_run.png")
        print("Screenshot saved to verification/focus_ring_run.png")

        browser.close()

if __name__ == "__main__":
    if not os.path.exists("verification"):
        os.makedirs("verification")
    run()
