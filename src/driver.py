from playwright.sync_api import sync_playwright, BrowserContext, BrowserType, Page, Playwright, Frame, Route, Request
from urllib.parse import urlparse
from parsel import Selector

from src.utils import Settings, logger
from src.models import ElementSelector



class PlaywrightDriver:
    """ Playwright with commonly used methods """


    def __init__(self, playwright: Playwright, context: BrowserContext, page: Page, settings: Settings) -> None:
        self.playwright = playwright
        self.context = context
        self.page = page
        self.timeout = settings.get("PLAYWRIGHT_NAVIGATION_TIMEOUT")
        self.settings = settings

    
    @classmethod
    def create_driver(
        cls,
        settings: Settings,
    ) -> "PlaywrightDriver":
        playwright = sync_playwright().start()
        browser_type : BrowserType = getattr(playwright, settings.get("PLAYWRIGHT_BROWSER_TYPE"))
        persistent_context = settings.get("PLAYWRIGHT_PERSISTENT_CONTEXT")
        if persistent_context:
            context = browser_type.launch_persistent_context(
                user_data_dir=persistent_context,
                **settings.get("PLAYWRIGHT_LAUNCH_ARGS")
            )
        else:
            browser = browser_type.launch(**settings.get("PLAYWRIGHT_LAUNCH_ARGS"))
            context = browser.new_context()
        page = context.new_page()
        driver = cls(playwright, context, page, settings)
        return driver
    

    def exists(self, el: ElementSelector, iframe: Frame = None) -> bool:
        target = iframe if iframe else self.page
        try:
            logger.debug(f"Attempting to find selector '{el.name}' in {'iframe' if iframe else 'page'}")
            count = target.locator(selector=el.value).count()
            exists = count > 0
            logger.debug(f"Selector '{el.name}' {'exists' if exists else 'does not exist'} (count: {count})")
            return exists
        except Exception as e:
            logger.error(f"Error in '{self.__class__.__name__}.{self.exists.__name__}' for selector '{el.name}': {str(e)}")
            return False


    def select_option(self, el: ElementSelector, option: str, iframe: Frame = None, wait_after: int = 1*1000) -> None:
        target = iframe if iframe else self.page
        try:
            self.wait_for_selector(el, iframe=iframe)
            logger.debug(f"Attempting to find selector '{el.name}' in {'iframe' if iframe else 'page'}")
            target.select_option(selector=el.value, value=option)
            logger.debug(f"Option '{option}' selected")
            target.wait_for_timeout(wait_after)
        except Exception as e:
            logger.error(f"Error in '{self.__class__.__name__}.{self.exists.__name__}' for selector '{el.name}': {str(e)}")


    def click(self, el: ElementSelector, wait_after: int = None, iframe: Frame = None, timeout: int = None) -> None:
        target = iframe if iframe else self.page
        try:
            logger.debug(f"Attempting to click selector '{el.name}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            target.click(selector=el.value, timeout=timeout)
            if wait_after is not None:
                target.wait_for_timeout(wait_after)
            logger.debug(f"Selector '{el.name}' clicked")
        except Exception as e:
            logger.error(f"Error in '{self.__class__.__name__}.{self.click.__name__}' for selector '{el.name}': {str(e)}")

    
    def fill(self, el: ElementSelector, value: str, wait_after: int = None, iframe: Frame = None, timeout: int = None) -> None:
        target = iframe if iframe else self.page
        try:
            logger.debug(f"Attempting to fill selector '{el.name}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            target.fill(selector=el.value, value=value, timeout=timeout)
            if wait_after is not None:
                target.wait_for_timeout(wait_after)
            logger.debug(f"Selector '{el.name}' filled")
        except Exception as e:
            logger.error(f"Error in '{self.__class__.__name__}.{self.fill.__name__}' for selector '{el.name}': {str(e)}")


    def wait_for_selector(self, el: ElementSelector, state: str = "visible", iframe: Frame = None, timeout: int = None) -> None:
        target = iframe if iframe else self.page
        try:
            logger.debug(f"Attempting to wait for '{el.name}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            target.wait_for_selector(selector=el.value, timeout=timeout, state=state)
            logger.debug(f"Selector '{el.name}' found (state: {state})")
        except Exception as e:
            logger.error(f"Error in '{self.__class__.__name__}.{self.wait_for_selector.__name__}' for selector '{el.name}': {str(e)}")

    
    def get_page(self, url: str, wait_el: ElementSelector = None, wait_after: int = 0, wait_until: str = "load", timeout: int = None) -> str:
        try:
            logger.debug(f"Attempting to navigate to '{url}'")
            timeout = self.timeout if timeout is None else timeout
            self.page.goto(url, timeout=timeout, wait_until=wait_until)
            if wait_el:
                self.wait_for_selector(el=wait_el, timeout=timeout)
            if wait_after:
                self.page.wait_for_timeout(wait_after)
            logger.debug(f"Successfully navigated to '{url}'")
            response = self.page.content()
            return response
        except Exception as e:
            logger.error(f"Error in '{self.__class__.__name__}.{self.get_page.__name__}' for URL '{url}': {str(e)}")
    

    def selector(self) -> Selector:
        content = self.page.content()
        return Selector(text=content)
    
    
    def block_resources(self, route: Route, request: Request) -> None:
        ad_domains = ['googletagmanager.com']
        request_domain = urlparse(request.url)
        if request.resource_type == "image" or any([domain for domain in ad_domains if domain in request_domain]):
            route.abort()
        else:
            route.continue_()


    def close(self) -> None:
        if hasattr(self, "browser"):
            try:
                self.context.close()
                logger.debug(f"Browser closed")
            except Exception as e:
                logger.error(f"Error in '{self.__class__.__name__}.{self.solve_captcha.__name__}': {str(e)}")
        if hasattr(self, "playwright"):
            try:
                self.playwright.stop()
            except Exception as e:
                logger.error(f"Error in '{self.__class__.__name__}.{self.solve_captcha.__name__}': {str(e)}")