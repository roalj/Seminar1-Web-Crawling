import hashlib

import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

TIMEOUT = 5


class SeleniumHelper:
    def __init__(self, url, driver):
        # driver = self.init_driver(url)
        # self.driver = driver
        driver.get(url)
        # Timeout needed for Web page to render
        time.sleep(TIMEOUT)
        self.links = self.get_links(driver, url)
        self.images = self.get_images(driver)
        self.content_type = driver.requests[0].response.headers['Content-Type']
        self.text = driver.page_source
        self.hash = hashlib.sha256(self.text.encode('utf-8')).hexdigest()
        self.status_code = driver.requests[0].response.status_code

    def get_links(self, driver):
        all_links = driver.find_elements_by_xpath("//a[@href]")
        return [x.get_attribute("href") for x in all_links]

    def get_images(self, driver):
        all_links = driver.find_elements_by_tag_name('img')
        return [x.get_attribute('src') for x in all_links]

    @staticmethod
    def init_driver():
        options = Options()
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)
        return driver
