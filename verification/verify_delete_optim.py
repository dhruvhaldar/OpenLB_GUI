from playwright.sync_api import sync_playwright, expect
import json
import time
import os
import sys

def run():
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Mock data
        cases = [
            {"id": "case1", "path": "/path/to/case1", "name": "case1", "domain": "domain1"},
            {"id": "case2", "path": "/path/to/case2", "name": "case2", "domain": "domain1"}
        ]

        # Call counters
        stats = {"get_cases": 0, "delete_cases": 0}

        def handle_get_cases(route):
            stats["get_cases"] += 1
            print(f"GET /cases called (Count: {stats['get_cases']})")
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps(cases)
            )

        def handle_delete_cases(route):
            stats["delete_cases"] += 1
            print(f"DELETE /cases called (Count: {stats['delete_cases']})")
            # Simulate success
            route.fulfill(
                status=200,
                content_type="application/json",
                body=json.dumps({"success": True})
            )

        def handle_request(route):
            # Check if it's the list cases call (GET /cases without query params ideally, but let's be loose)
            if route.request.method == "GET" and "/cases" in route.request.url and "case_path" not in route.request.url:
                handle_get_cases(route)
            elif route.request.method == "DELETE":
                handle_delete_cases(route)
            else:
                route.continue_()

        # Setup routes
        page.route("**/cases*", handle_request)

        # Mock config to avoid errors
        page.route("**/config*", lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps({"content": ""})))

        # Mock build/run to avoid errors if triggered
        page.route("**/build", lambda r: r.fulfill(status=200, body=json.dumps({"success": True})))
        page.route("**/run", lambda r: r.fulfill(status=200, body=json.dumps({"success": True})))

        print("Navigating to app...")
        try:
            page.goto("http://localhost:4173")
        except Exception as e:
            print(f"Failed to navigate: {e}")
            sys.exit(1)

        # Wait for cases to load
        print("Waiting for case1...")
        try:
            page.wait_for_selector("text=case1", timeout=5000)
        except Exception:
            print("Timeout waiting for case1. Backend mock might be failing.")
            page.screenshot(path="verification/error_load.png")
            sys.exit(1)

        initial_get_count = stats["get_cases"]
        print(f"Initial GET /cases count: {initial_get_count}")

        # Select case1
        print("Selecting case1...")
        page.click("text=case1")

        # Click Delete button (Trash2 icon)
        # The button has title "Delete Case"
        print("Clicking Delete button...")
        try:
            page.get_by_role("button", name="Delete Case").click()
        except Exception:
            print("Could not find Delete button.")
            page.screenshot(path="verification/error_delete_btn.png")
            sys.exit(1)

        # Wait for modal
        print("Waiting for modal...")
        # Check for text in the modal body, e.g. "Are you sure you want to delete case1?"
        # We look for "case1" inside a modal.
        try:
            page.wait_for_selector("text=Are you sure you want to delete", timeout=5000)
            page.wait_for_selector("text=case1", timeout=5000)
        except Exception:
            print("Timeout waiting for modal content.")
            page.screenshot(path="verification/error_modal.png")
            sys.exit(1)

        # Click Confirm in modal
        # The modal has a button "Delete" which is red.
        print("Confirming delete...")
        page.get_by_role("button", name="Delete", exact=True).click()

        # Wait for DELETE request to complete and UI to update
        print("Waiting for case1 to disappear...")
        try:
            expect(page.locator("text=case1")).not_to_be_visible(timeout=5000)
        except AssertionError:
            print("case1 did not disappear!")
            page.screenshot(path="verification/error_not_disappeared.png")
            sys.exit(1)

        # Wait a bit to see if a re-fetch happens
        print("Waiting for potential re-fetch...")
        page.wait_for_timeout(2000)

        final_get_count = stats["get_cases"]
        print(f"Final GET /cases count: {final_get_count}")

        if final_get_count > initial_get_count:
            print(f"FAILURE: GET /cases was called after delete. (Calls: {initial_get_count} -> {final_get_count})")
            sys.exit(1)
        else:
            print("SUCCESS: GET /cases was NOT called after delete.")
            page.screenshot(path="verification/success_after_delete.png")
            sys.exit(0)

if __name__ == "__main__":
    if not os.path.exists("verification"):
        os.makedirs("verification")
    run()
