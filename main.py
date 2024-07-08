from src.driver import WebDriver
from playwright.async_api import async_playwright
import asyncio


async def crawl():
    playwright = await async_playwright().start()
    driver = await WebDriver.create_driver(
        playwright=playwright,
        browser_launch_type="chromium",
        launch_args=dict(
            headless=False,
        ),
        timeout=60*1000
    )
    await driver.get_page("https://google.com/")
    await driver.close()

asyncio.run(crawl())
