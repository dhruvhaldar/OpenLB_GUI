import subprocess
import time
import os
import signal
from playwright.sync_api import sync_playwright
import json
import sys

def verify_case_count():
    # Start the frontend server
    print("Starting frontend server...")
    # Using pnpm preview to serve the build
    # cwd needs to be openlb-gui/frontend
    frontend_process = subprocess.Popen(
        ["pnpm", "preview", "--port", "5173", "--strictPort"],
        cwd="openlb-gui/frontend",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid # To kill the process group later
    )

    # Wait for server to start
    # We can try to connect to the socket to ensure it's up, or just sleep
    time.sleep(5)

    try:
        with sync_playwright() as p:
            print("Launching browser...")
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Mock the /cases endpoint
            cases = []
            for i in range(10):
                cases.append({
                    "id": f"case-{i}",
                    "path": f"/path/to/case-{i}",
                    "name": f"case-{i}",
                    "domain": "TestDomain"
                })

            def handle_cases(route):
                route.fulfill(
                    status=200,
                    content_type="application/json",
                    body=json.dumps(cases)
                )

            # Route requests
            page.route("**/cases", handle_cases)
            # Mock config to avoid errors if the app tries to load it
            page.route("**/config?*", lambda route: route.fulfill(status=200, body=json.dumps({"content": ""})))

            print("Navigating to http://localhost:5173...")
            try:
                page.goto("http://localhost:5173")
            except Exception as e:
                print(f"Failed to navigate: {e}")
                # Check server output
                out, err = frontend_process.communicate(timeout=1)
                print(f"Server stdout: {out.decode()}")
                print(f"Server stderr: {err.decode()}")
                sys.exit(1)

            # Wait for the heading to appear
            heading_selector = "#cases-heading"
            try:
                page.wait_for_selector(heading_selector, timeout=5000)
            except Exception:
                print("Heading not found. Dumping page content:")
                print(page.content())
                sys.exit(1)

            # Get text content
            text = page.locator(heading_selector).text_content()
            print(f"Initial Heading Text: '{text}'")

            # Verify it contains "10"
            if "10" in text:
                print("PASS: Initial count is correct (10)")
            else:
                print(f"FAIL: Expected '10' in heading, got '{text}'")
                # Save screenshot
                page.screenshot(path="verification/fail_initial.png")
                sys.exit(1)

            # Filter for "case-1"
            print("Typing filter 'case-1'...")
            page.fill("input[placeholder*='Filter']", "case-1")

            # Wait a bit for debounce and render (Sidebar uses useDeferredValue)
            time.sleep(2)

            # Verify text content update
            text_filtered = page.locator(heading_selector).text_content()
            print(f"Filtered Heading Text: '{text_filtered}'")

            # Should be "1/10"
            if "1/10" in text_filtered:
                 print("PASS: Filtered count is correct (1/10)")
            else:
                 print(f"FAIL: Expected '1/10' in heading, got '{text_filtered}'")
                 page.screenshot(path="verification/fail_filtered.png")
                 sys.exit(1)

            browser.close()

    finally:
        print("Stopping frontend server...")
        try:
            os.killpg(os.getpgid(frontend_process.pid), signal.SIGTERM)
            frontend_process.wait(timeout=5)
        except Exception:
            pass

if __name__ == "__main__":
    verify_case_count()
