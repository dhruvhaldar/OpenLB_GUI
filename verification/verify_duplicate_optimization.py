import time
import json
from playwright.sync_api import sync_playwright

def verify_duplicate_optimization():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()

        # Mock APIs
        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([{
                "id": "case1",
                "path": "/cases/case1",
                "name": "case1",
                "domain": "Default"
            }])
        ))

        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"content": "<xml/>"})
        ))

        duplicate_request_data = {}
        def handle_duplicate(route):
            nonlocal duplicate_request_data
            duplicate_request_data = json.loads(route.request.post_data)
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({
                    "success": True,
                    "case": {
                        "id": "case1_copy",
                        "path": "/cases/case1_copy",
                        "name": duplicate_request_data["new_name"],
                        "domain": "Default"
                    }
                })
            )

        page.route("**/cases/duplicate", handle_duplicate)

        # Navigate to app
        try:
            page.goto("http://localhost:4173")
        except Exception:
             print("Could not connect to localhost:4173. Make sure 'pnpm preview' is running.")
             return

        # Select case
        page.get_by_text("case1").click()

        # Open Duplicate Modal - Be specific to the button in header
        # Using get_by_role('button', name='Duplicate Case')
        page.get_by_role("button", name="Duplicate Case").click()

        # Verify initial name (case1_copy)
        input_field = page.get_by_label("New Case Name")
        input_value = input_field.input_value()
        if input_value != "case1_copy":
            print(f"FAILED: Initial name incorrect. Expected 'case1_copy', got '{input_value}'")
            browser.close()
            return

        # Type new name
        input_field.fill("optimized_case")

        # Verify input updated
        if input_field.input_value() != "optimized_case":
            print(f"FAILED: Input not updating. Got '{input_field.input_value()}'")
            browser.close()
            return

        # Submit - Use strict button selector inside dialog if needed, but 'Duplicate' name is unique in dialog
        page.get_by_role("button", name="Duplicate", exact=True).click()

        # Verify API request
        if duplicate_request_data.get("new_name") == "optimized_case":
            print("SUCCESS: Duplicate request sent with correct name.")
        else:
            print(f"FAILED: Request sent with wrong name: {duplicate_request_data.get('new_name')}")

        browser.close()

if __name__ == "__main__":
    verify_duplicate_optimization()
