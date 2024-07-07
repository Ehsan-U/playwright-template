import random
from typing import Dict
from parsel import Selector
from src.logger import logger
from undetected_playwright.async_api import Frame, Response, BrowserContext, Page, Playwright, BrowserType




class WebDriver:
    """ Common usage of playwright"""


    def __init__(self, context: BrowserContext, page: Page, timeout: int) -> None:
        self.context = context
        self.page = page
        self.timeout = timeout


    @classmethod
    async def create_driver(
        cls,
        playwright: Playwright,
        browser_launch_type: str,
        launch_args: Dict,
        timeout: int
    ):
        browser_type: BrowserType = getattr(playwright, browser_launch_type)
        browser = await browser_type.launch(**launch_args)
        context = await browser.new_context()
        page = await context.new_page()
        driver = cls(context=context, page=page, timeout=timeout)
        return driver
    

    async def exists(self, selector: str, iframe: Frame = None) -> bool:
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.exists.__name__}"
        try:
            logger.debug(f"Attempting to find selector '{selector}' in {'iframe' if iframe else 'page'}")
            count = await target.locator(selector=selector).count()
            exists = count > 0
            logger.debug(f"Selector '{selector}' {'exists' if exists else 'does not exist'} (count: {count})")
            return exists
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for selector '{selector}': {str(e)}")
            return False


    async def click(self, selector: str, wait_after: int = None, iframe: Frame = None, timeout: int = None):
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.click.__name__}"
        try:
            logger.debug(f"Attempting to click selector '{selector}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            await target.click(selector, timeout=timeout)
            if wait_after is not None:
                await self.page.wait_for_timeout(wait_after)
            logger.debug(f"Selector '{selector}' clicked")
            return True
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for selector '{selector}': {str(e)}")
            return False
        

    async def wait_for_selector(self, selector: str, state: str = "visible", iframe: Frame = None, timeout: int = None):
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.wait_for_selector.__name__}"
        try:
            logger.debug(f"Attempting to wait for '{selector}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            await target.wait_for_selector(selector=selector, timeout=timeout, state=state)
            logger.debug(f"Selector '{selector}' found (state: {state})")
            return True
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for selector '{selector}': {str(e)}")
            return False


    async def get_page(self, url: str, wait_selector: str = None, wait_after: int = 0, wait_until: str = "load", callback: callable = None, timeout: int = None, **kwargs) -> Response:
        action_name = f"{self.__class__.__name__}.{self.get_page.__name__}"
        try:
            logger.debug(f"Attempting to navigate to '{url}'")
            timeout = self.timeout if timeout is None else timeout
            response = await self.page.goto(url, timeout=timeout, wait_until=wait_until)
            if wait_selector:
                await self.wait_for_selector(wait_selector, timeout)
            if wait_after:
                await self.page.wait_for_timeout(wait_after)
            if callback is not None:
                logger.debug("Executing callback function")
                await callback(**kwargs)
                if wait_selector:
                    await self.wait_for_selector(wait_selector, timeout)
            logger.debug(f"Successfully navigated to '{url}'")
            return response
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for URL '{url}': {str(e)}")
            return None
        

    async def sleep(self, a: float, b: float):
        await self.page.wait_for_timeout(random.uniform(a, b)*1000)


    async def selector(self) -> Selector:
        content = await self.page.content()
        return Selector(text=content)
    

    async def close(self):
        action_name = f"{self.__class__.__name__}.{self.close.__name__}"
        if hasattr(self, "browser"):
            try:
                await self.context.close()
                logger.debug(f"Browser closed")
            except Exception as e:
                logger.exception(f"Error in '{action_name}': {str(e)}")





    