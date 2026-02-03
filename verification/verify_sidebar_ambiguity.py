
import asyncio
from playwright.async_api import async_playwright, expect

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Mock API to return ambiguous cases
        await page.route("**/cases", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='[{"id": "1", "name": "flow", "domain": "cylinder", "path": "/tmp/1"}, {"id": "2", "name": "flow", "domain": "channel", "path": "/tmp/2"}]'
        ))

        # Mock Config API to avoid 404s
        await page.route("**/config?*", lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            body='{"content": ""}'
        ))

        try:
            await page.goto("http://localhost:5173", timeout=5000)
        except:
             print("Could not connect to localhost:5173. Make sure the frontend server is running.")
             return

        # Wait for cases to load
        await expect(page.locator("aside ul")).to_be_visible()

        items = page.locator("aside ul li button")
        await expect(items).to_have_count(2)

        item1 = items.nth(0)

        # Check title attribute
        title1 = await item1.get_attribute("title")
        print(f"Item 1 Title: {title1}")

        # Check aria-label
        aria1 = await item1.get_attribute("aria-label")
        print(f"Item 1 Aria-Label: {aria1}")

        if title1 == "cylinder / flow" and aria1 == "cylinder / flow":
            print("SUCCESS: Title and Aria-Label include domain.")
        else:
            print("FAIL: Title or Aria-Label incorrect.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
