from playwright.sync_api import sync_playwright, expect
import json
import time

def test_sidebar_limit():
    with sync_playwright() as p:
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Create 1000 cases
        cases = []
        for i in range(1000):
            cases.append({
                "id": f"case-{i}",
                "path": f"/path/to/case-{i}",
                "name": f"case-{i:04d}", # pad with zeros for sorting
                "domain": "TestDomain"
            })

        # Sort cases
        cases.sort(key=lambda x: x["name"])

        def handle_cases(route):
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(cases)
            )

        page.route("**/cases", handle_cases)
        page.route("**/config?*", lambda route: route.fulfill(status=200, content_type="application/json", body=json.dumps({"content": ""})))

        print("Navigating to frontend...")
        try:
            page.goto("http://localhost:5173", timeout=30000)
        except Exception as e:
            print(f"Failed to navigate: {e}")
            print("Make sure the frontend server is running on port 5173")
            browser.close()
            exit(1)

        # Wait for cases to load
        print("Waiting for cases...")
        try:
            page.wait_for_selector("text=case-0000", timeout=10000)
        except Exception:
            print("Timeout waiting for case list to load")
            page.screenshot(path="verification/timeout.png")
            browser.close()
            exit(1)

        # Count list items
        list_items = page.locator("nav ul li button")
        count = list_items.count()
        print(f"List item count: {count}")

        # Check the counter text
        counter = page.locator("#cases-heading + span")
        counter_text = counter.text_content()
        print(f"Counter text: {counter_text}")

        # Verification logic
        if count > 200:
            print(f"BASELINE: Rendering {count} items (unoptimized)")
        else:
            print(f"OPTIMIZED: Rendering {count} items")
            if "1000" in counter_text:
                 print("PASS: Counter shows total match count")
            else:
                 print("FAIL: Counter does NOT show total match count")

        # Take screenshot for verification
        page.screenshot(path="verification/sidebar_limit.png")
        print("Screenshot saved to verification/sidebar_limit.png")

        browser.close()

if __name__ == "__main__":
    test_sidebar_limit()
