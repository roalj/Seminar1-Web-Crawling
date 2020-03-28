import hashlib
import time
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options


class SeleniumHelper:
    def __init__(self, url, thread_name):
        # driver = self.init_driver(url)
        # self.driver = driver
        start_time = time.time()

        driver = SeleniumHelper.init_driver()
        #time.sleep(1)
        driver.get(url)
        time.sleep(1)
        print("--- %s AFTER SELENIUm, thread name: %s ---" % (time.time() - start_time, thread_name))

        start_time1 = time.time()

        self.links = self.get_links(driver)
        self.images = self.get_images(driver)
        self.content_type = driver.requests[0].response.headers['Content-Type']
        print("--- %s GET LINKS," % (time.time() - start_time1))

        self.text = driver.page_source
        self.hash = hashlib.sha256(self.text.encode('utf-8')).hexdigest()
        self.status_code = driver.requests[0].response.status_code
        print("--- %s AFTER SELENIUm 222222 thread name: %s ---" % (time.time() - start_time, thread_name))
        driver.close()


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



