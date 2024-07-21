import random
from typing import Dict
from urllib.parse import urlparse
from parsel import Selector
from src.utils import logger, ElementSelector
from playwright.async_api import Frame, Response, BrowserContext, Page, Playwright, BrowserType, Route, Request



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
        timeout: int,
        block_resources: bool = False
    ):
        browser_type: BrowserType = getattr(playwright, browser_launch_type)
        browser = await browser_type.launch(**launch_args)
        context = await browser.new_context()
        page = await context.new_page()
        driver = cls(context=context, page=page, timeout=timeout)
        if block_resources:
            await driver.page.route("**/*", driver.block_resources)
        return driver
    

    async def exists(self, el: ElementSelector, iframe: Frame = None) -> bool:
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.exists.__name__}"
        try:
            logger.debug(f"Attempting to find selector '{el.name}' in {'iframe' if iframe else 'page'}")
            count = await target.locator(selector=el.value).count()
            exists = count > 0
            logger.debug(f"Selector '{el.name}' {'exists' if exists else 'does not exist'} (count: {count})")
            return exists
        except Exception as e:
            logger.debug(f"Error in '{action_name}' for selector '{el.name}': {str(e)}")
            return False


    async def click(self, el: ElementSelector, wait_after: int = None, iframe: Frame = None, timeout: int = None) -> bool:
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.click.__name__}"
        try:
            logger.debug(f"Attempting to click selector '{el.name}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            await target.click(selector=el.value, timeout=timeout)
            if wait_after is not None:
                await self.page.wait_for_timeout(wait_after)
            logger.debug(f"Selector '{el.name}' clicked")
            return True
        except Exception as e:
            logger.debug(f"Error in '{action_name}' for selector '{el.name}': {str(e)}")
            return False


    async def fill(self, el: ElementSelector, value: str, wait_after: int = None, iframe: Frame = None, timeout: int = None) -> bool:
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.fill.__name__}"
        try:
            logger.debug(f"Attempting to fill selector '{el.name}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            await target.fill(selector=el.value, value=value, timeout=timeout)
            if wait_after is not None:
                await self.page.wait_for_timeout(wait_after)
            logger.debug(f"Selector '{el.name}' filled")
            return True
        except Exception as e:
            logger.debug(f"Error in '{action_name}' for selector '{el.name}': {str(e)}")
            return False


    async def wait_for_selector(self, el: ElementSelector, state: str = "visible", iframe: Frame = None, timeout: int = None) -> bool:
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.wait_for_selector.__name__}"
        try:
            logger.debug(f"Attempting to wait for '{el.name}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            await target.wait_for_selector(selector=el.value, timeout=timeout, state=state)
            logger.debug(f"Selector '{el.name}' found (state: {state})")
            return True
        except Exception as e:
            logger.debug(f"Error in '{action_name}' for selector '{el.name}': {str(e)}")
            return False


    async def get_page(self, url: str, wait_el: ElementSelector = None, wait_after: int = 0, wait_until: str = "load", callback: callable = None, timeout: int = None, **kwargs) -> Response:
        action_name = f"{self.__class__.__name__}.{self.get_page.__name__}"
        try:
            logger.debug(f"Attempting to navigate to '{url}'")
            timeout = self.timeout if timeout is None else timeout
            response = await self.page.goto(url, timeout=timeout, wait_until=wait_until)
            if wait_el:
                await self.wait_for_selector(el=wait_el, timeout=timeout)
            if wait_after:
                await self.page.wait_for_timeout(wait_after)
            if callback is not None:
                logger.debug("Executing callback function")
                await callback(**kwargs)
                if wait_el:
                    await self.wait_for_selector(el=wait_el, timeout=timeout)
            logger.debug(f"Successfully navigated to '{url}'")
            return response
        except Exception as e:
            logger.debug(f"Error in '{action_name}' for URL '{url}': {str(e)}")
            return None
        

    async def sleep(self, a: float, b: float) -> None:
        await self.page.wait_for_timeout(random.uniform(a, b)*1000)


    async def type(self, el: ElementSelector, value: str) -> None:
        await self.page.type(el.value, value)
        

    async def selector(self, iframe: Frame = None) -> Selector:
        target = iframe if iframe else self.page
        content = await target.content()
        return Selector(text=content)
    

    async def block_resources(self, route: Route, request: Request):
        ad_domains = ['googletagmanager.com']
        request_domain = urlparse(request.url)
        if request.resource_type == "image" or any([domain for domain in ad_domains if domain in request_domain]):
            await route.abort()
        else:
            await route.continue_()
    

    async def close(self) -> None:
        action_name = f"{self.__class__.__name__}.{self.close.__name__}"
        if hasattr(self, "browser"):
            try:
                await self.context.close()
                logger.debug(f"Browser closed")
            except Exception as e:
                logger.debug(f"Error in '{action_name}': {str(e)}")