from src.driver import WebDriver



driver = WebDriver.create()
driver.get_page("https://google.com/")
driver.close()