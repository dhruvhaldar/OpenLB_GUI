from playwright.sync_api import sync_playwright, expect
import json

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        cases = [
            {"id": "c1", "path": "/c1", "name": "case-1", "domain": "d1"}
        ]

        # Serve cases
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps(cases)
        ))

        # Mock DELETE
        def handle_delete(route):
            # After delete, subsequent GET cases returns empty list
            cases.clear()
            route.fulfill(status=200, body=json.dumps({"success": True}))

        page.route("**/cases?case_path=*", handle_delete)

        # Mock config to avoid errors
        page.route("**/config*", lambda r: r.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"content": "foo"})
        ))

        print("Navigating...")
        page.goto("http://localhost:4173")

        # Select case
        page.click("text=case-1")

        # Click Delete (Trash icon)
        print("Clicking Delete...")
        page.get_by_role("button", name="Delete Case").click()

        # Wait for modal
        print("Waiting for modal...")
        expect(page.get_by_role("dialog", name="Delete Case")).to_be_visible()

        # Click Confirm Delete
        print("Confirming delete...")
        page.get_by_role("button", name="Delete", exact=True).click()

        # Wait for modal to disappear
        expect(page.get_by_role("dialog")).to_be_hidden()

        # Wait a bit for React to render the "No Case Selected" view
        page.wait_for_timeout(500)

        # Check focus
        active_tag = page.evaluate("document.activeElement.tagName")
        active_id = page.evaluate("document.activeElement.id")

        print(f"Active element: {active_tag} id='{active_id}'")

        if active_tag == "BODY":
            print("FAIL: Focus dropped to body")
        elif active_id == "main-content":
            print("PASS: Focus restored to main-content")
        else:
            print(f"INFO: Focus is on {active_tag}#{active_id}")

        browser.close()

if __name__ == "__main__":
    run()
