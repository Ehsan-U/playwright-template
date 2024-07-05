from abc import ABC, abstractmethod
import json
from pathlib import Path
import pickle
import random
from typing import Dict, List

from parsel import Selector
from src.logger import logger
from playwright.sync_api import Frame, Response, PlaywrightContextManager, BrowserContext, Page, Browser
from browserforge.fingerprints import FingerprintGenerator, Fingerprint



class PlaywrightFactory(ABC):
    @abstractmethod
    def get_sync_playwright(self) -> PlaywrightContextManager:
        pass

    @abstractmethod
    def get_fingerprint_injector(self) -> BrowserContext:
        pass


class RegularPlaywrightFactory(PlaywrightFactory):
    def get_sync_playwright(self):
        from playwright.sync_api import sync_playwright
        return sync_playwright()

    def get_fingerprint_injector(self):
        from browserforge.injectors.playwright import NewContext
        return NewContext


class UndetectedPlaywrightFactory(PlaywrightFactory):
    def get_sync_playwright(self):
        from undetected_playwright.sync_api import sync_playwright
        return sync_playwright()

    def get_fingerprint_injector(self):
        from browserforge.injectors.undetected_playwright import NewContext
        return NewContext



class WebDriver:
    """ Common usage of playwright"""


    def __init__(self, factory: PlaywrightFactory) -> None:
        self.playwright = factory.get_sync_playwright().start()
        self.inject_fingerprint = factory.get_fingerprint_injector()
        self.context: BrowserContext = None
        self.page: Page = None
        self.timeout: int = None
        self.fingerprint: Fingerprint = None
        self.cookies: List[dict] = []


    @classmethod
    def create(
        cls,
        browser_launch_type: str = "chromium",
        profile: str = None,
        headless: bool = True,
        channel: str = "chrome",
        proxy: dict = None,
        args: List[str] = None,
        block_ads: bool = False,
        timeout: int = 30*1000,
        use_undetected: bool = False # only works with chrome
    ):
        factory = UndetectedPlaywrightFactory() if use_undetected else RegularPlaywrightFactory()
        driver = cls(factory)

        browser_type = getattr(driver.playwright, browser_launch_type)
        launch_kwargs = {
            "headless": headless,
            "proxy": proxy,
            "args": args or [],
        }

        if browser_launch_type == "chromium":
            launch_kwargs["channel"] = channel
            if block_ads:
                launch_kwargs["args"].extend([
                    "--disable-extensions-except=.extensions/ublock/",
                    "--load-extension=.extensions/ublock/",
                ])

        browser: Browser = browser_type.launch(**launch_kwargs)

        driver.load_profile(profile)
        if driver.fingerprint is None:
            driver.fingerprint =  FingerprintGenerator().generate(
                browser=['chrome','firefox','edge','safari'], 
                os=['windows','linux','macos'], 
                device=['desktop'], 
                locale=['en-US','en']
            )      
        driver.context = driver.inject_fingerprint(browser, fingerprint=driver.fingerprint)
        driver.context.add_cookies(driver.cookies)

        driver.page = driver.context.new_page()
        driver.timeout = timeout
        return driver


    def exists(self, selector: str, iframe: Frame = None) -> bool:
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.exists.__name__}"
        try:
            logger.debug(f"Attempting to find selector '{selector}' in {'iframe' if iframe else 'page'}")
            count = target.locator(selector=selector).count()
            exists = count > 0
            logger.debug(f"Selector '{selector}' {'exists' if exists else 'does not exist'} (count: {count})")
            return exists
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for selector '{selector}': {str(e)}")
            return False


    def click(self, selector: str, wait_after: int = None, iframe: Frame = None, timeout: int = None):
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.click.__name__}"
        try:
            logger.debug(f"Attempting to click selector '{selector}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            target.click(selector, timeout=timeout)
            if wait_after is not None:
                self.page.wait_for_timeout(wait_after)
            logger.debug(f"Selector '{selector}' clicked")
            return True
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for selector '{selector}': {str(e)}")
            return False
        

    def wait_for_selector(self, selector: str, state: str = "visible", iframe: Frame = None, timeout: int = None):
        target = iframe if iframe else self.page
        action_name = f"{self.__class__.__name__}.{self.wait_for_selector.__name__}"
        try:
            logger.debug(f"Attempting to wait for '{selector}' in {'iframe' if iframe else 'page'}")
            timeout = self.timeout if timeout is None else timeout
            target.wait_for_selector(selector=selector, timeout=timeout, state=state)
            logger.debug(f"Selector '{selector}' found (state: {state})")
            return True
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for selector '{selector}': {str(e)}")
            return False


    def get_page(self, url: str, wait_selector: str = None, wait_after: int = 0, wait_until: str = "load", callback: callable = None, timeout: int = None, **kwargs) -> Response:
        action_name = f"{self.__class__.__name__}.{self.get_page.__name__}"
        try:
            logger.debug(f"Attempting to navigate to '{url}'")
            timeout = self.timeout if timeout is None else timeout
            response = self.page.goto(url, timeout=timeout, wait_until=wait_until)
            if wait_selector:
                self.wait_for_selector(wait_selector, timeout)
            if wait_after:
                self.page.wait_for_timeout(wait_after)
            if callback is not None:
                logger.debug("Executing callback function")
                callback(**kwargs)
                if wait_selector:
                    self.wait_for_selector(wait_selector, timeout)
            logger.debug(f"Successfully navigated to '{url}'")
            return response
        except Exception as e:
            logger.exception(f"Error in '{action_name}' for URL '{url}': {str(e)}")
            return None
        

    def sleep(self, a: float, b: float):
        self.page.wait_for_timeout(random.uniform(a, b)*1000)


    @property
    def selector(self) -> Selector:
        content = self.page.content()
        return Selector(text=content)
    

    @property
    def headers(self) -> Dict:
        return self.fingerprint.headers


    def close(self):
        action_name = f"{self.__class__.__name__}.{self.close.__name__}"
        if hasattr(self, "browser"):
            try:
                self.context.close()
                self.playwright.stop()
                logger.debug(f"Browser closed")
            except Exception as e:
                logger.exception(f"Error in '{action_name}': {str(e)}")


    def save_profile(self, name: str):
        path = Path(".profiles") / name
        path.mkdir(parents=True, exist_ok=True)
        action_name = f"{self.__class__.__name__}.{self.save_profile.__name__}"
        try:
            logger.debug(f"Attempting to save profile '{name}'")
            
            fingerprint_path = path / "fingerprint.pkl"
            cookies_path = path / "cookies.json"
            with fingerprint_path.open('wb') as f:
                pickle.dump(self.fingerprint, f)
            with cookies_path.open('w') as f:
                json.dump(self.context.cookies(), f)

            logger.debug(f"Successfully saved profile '{name}'")
        except Exception as e:
            logger.exception(f"Error in '{action_name}': {str(e)}")


    def load_profile(self, name: str):
        try:
            logger.debug(f"Attempting to load profile '{name}'")
            
            path = Path(".profiles") / name
            fingerprint_path = path / "fingerprint.pkl"
            cookies_path = path / "cookies.json"
            if not fingerprint_path.exists():
                raise FileNotFoundError(f"Fingerprint file not found: {fingerprint_path}")
            if not cookies_path.exists():
                raise FileNotFoundError(f"Cookies file not found: {cookies_path}")
            with fingerprint_path.open('rb') as f:
                self.fingerprint = pickle.load(f)
            with cookies_path.open('r') as f:
                self.cookies = json.load(f)

            logger.debug(f"Successfully loaded profile '{name}'")
        except Exception as e:
            logger.debug(f"Creating new profile '{name}'")

    
    def get_profiles(self) -> List[str]:
        path: Path = Path(".profiles")
        action_name = f"{self.__class__.__name__}.{self.get_profiles.__name__}"
        try:
            logger.debug(f"Attempting to get profiles")
            profiles = [d.name for d in path.iterdir() if d.is_dir()]
            logger.debug(f"Successfully get profiles")
            return profiles
        except Exception as e:
            logger.exception(f"Error in '{action_name}': {str(e)}")