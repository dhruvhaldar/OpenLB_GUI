import time
from playwright.sync_api import sync_playwright, expect
import os
import json

def verify_save_button():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(permissions=['clipboard-read', 'clipboard-write'])
        page = context.new_page()

        page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps([
                {"id": "test-case", "name": "test_case", "path": "/mock/test_case", "domain": "Test"}
            ])
        ))

        page.route("**/config?path=*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"case_path": "/mock/test_case", "content": "Initial content"})
        ))

        mock_fail = True
        def handle_post_config(route):
            nonlocal mock_fail
            if mock_fail:
                route.fulfill(status=500, body=json.dumps({"detail": "Mock failure"}))
                mock_fail = False
            else:
                route.fulfill(status=200, body=json.dumps({"message": "Saved"}))

        page.route("**/config", lambda route: handle_post_config(route) if route.request.method == "POST" else route.continue_())

        try:
            page.goto("http://localhost:5173")
            page.get_by_text("test_case").click()
            expect(page.get_by_label("Configuration")).to_be_visible()

            textarea = page.get_by_label("Configuration")
            textarea.fill("New content")

            # Find button by shortcut attribute which is stable
            save_btn = page.locator('button[aria-keyshortcuts="Control+S"]')
            save_btn.click()

            # Expect "Failed" state (after my fix)
            expect(page.get_by_text("Failed")).to_be_visible()

            # Verify Title
            title = save_btn.get_attribute("title")
            print(f"Error State Title: {title}")

            # Expect title to contain 'Failed' or 'retry'
            if "Failed" not in title and "retry" not in title:
                 print("WARNING: Title does not indicate failure")

            page.screenshot(path="/home/jules/verification/save_failed_state.png")

            # Click again to succeed
            save_btn.click()

            # Expect "Saved" state
            expect(page.get_by_text("Saved")).to_be_visible()

            title = save_btn.get_attribute("title")
            print(f"Success State Title: {title}")

            if "Saved" not in title:
                print("WARNING: Title does not indicate success")

            page.screenshot(path="/home/jules/verification/save_success_state.png")

        except Exception as e:
            print(f"Test failed: {e}")
            page.screenshot(path="/home/jules/verification/failure.png")
            raise e
        finally:
            browser.close()

if __name__ == "__main__":
    os.makedirs("/home/jules/verification", exist_ok=True)
    verify_save_button()
