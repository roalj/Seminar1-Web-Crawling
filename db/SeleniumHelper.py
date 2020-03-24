import hashlib

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumHelper:
    def __init__(self, url, driver):
        # driver = self.init_driver(url)
        # self.driver = driver
        driver.get(url)
        self.links = driver.find_elements_by_xpath("//a[@href]")
        self.images = driver.find_elements_by_tag_name('img')
        self.content_type = driver.requests[0].response.headers['Content-Type']
        self.text = driver.page_source
        self.hash = hashlib.sha256(self.text.encode('utf-8')).hexdigest()
        self.status_code = driver.requests[0].response.status_code

    @staticmethod
    def init_driver():
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        return driver



