from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.expected_conditions import staleness_of


class wait_page_load:
    def __init__(self, browser, timeout=5):
        self.browser = browser
        self.timeout = timeout

    def __enter__(self):
        self.old_page = self.browser.find_element(By.TAG_NAME, 'html')

    def __exit__(self, *_):
        WebDriverWait(self.browser, self.timeout).until(staleness_of(self.old_page))
