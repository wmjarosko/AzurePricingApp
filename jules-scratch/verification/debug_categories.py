import asyncio
from playwright.async_api import async_playwright, expect

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        # Navigate to the local HTML file
        await page.goto("file:///app/index.html")

        # Give the DOM a moment to load and the initial rows to generate
        await page.wait_for_timeout(1000)

        # Take a screenshot of the initial state
        await page.screenshot(path="jules-scratch/verification/initial_state.png", full_page=True)

        await browser.close()

asyncio.run(main())
