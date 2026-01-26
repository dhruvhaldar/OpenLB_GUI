from playwright.sync_api import Page, expect, sync_playwright
import time

def test_cases_list(page: Page):
    # 1. Go to the app
    page.goto("http://localhost:5173")

    # 2. Wait for cases to load
    page.wait_for_selector("aside nav ul li button", state="visible", timeout=10000)

    # 3. Take screenshot
    page.screenshot(path="/home/jules/verification/verification.png")

    # 4. Assert cases are visible
    expect(page.locator("aside nav ul")).to_contain_text("some_case")
    expect(page.locator("aside nav ul")).to_contain_text("cyl_flow")

if __name__ == "__main__":
    import os
    os.makedirs("/home/jules/verification", exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_cases_list(page)
            print("Verification successful!")
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/error.png")
        finally:
            browser.close()
