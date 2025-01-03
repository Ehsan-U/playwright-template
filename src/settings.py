import os
import dotenv
dotenv.load_dotenv()


# captcha solver key
TWO_CAPTCHA_API_KEY = os.getenv("TWO_CAPTCHA_API_KEY")

# Playwright
PLAYWRIGHT_NAVIGATION_TIMEOUT = 60*1000
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_PERSISTENT_CONTEXT = ".dir"
PLAYWRIGHT_LAUNCH_ARGS = {
    "headless": True
}

# concurrency for downloading files
CONCURRENT_REQUESTS = 8