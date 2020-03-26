import time
from queue import Queue
from urllib.request import urlparse, urljoin
import requests
import psycopg2
import hashlib
import threading

from db.SeleniumHelper import SeleniumHelper

url_queue = Queue()
already_visited_sites = set()
content_types = ['PDF', 'DOC', 'DOCX', 'PPT', 'PPTX']
current_searched_websites = []


def is_site_in_db(base_url, cur):
    sql = "SELECT id FROM crawldb.site where domain = %s"
    cur.execute(sql, (base_url,))
    record_exists = cur.fetchone()
    return record_exists

# test
def delete_all_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM crawldb.image")
    cur.execute("DELETE FROM crawldb.page_data")
    cur.execute("DELETE FROM crawldb.page")
    cur.execute("DELETE FROM crawldb.site")
    cur.close


def is_page_alread_saved(url, cur):
    sql = "SELECT id FROM crawldb.page where url = %s"
    cur.execute(sql, (url,))
    record_exists = cur.fetchone()
    return record_exists


def add_new_domains_to_queue(url, new_urls):
    base_url = get_base_url(url)
    for a in new_urls.copy():
        if not a.startswith(base_url):
            new_link = get_base_url(a)
            if new_link not in already_visited_sites:
                workQueue.put(new_link)
                already_visited_sites.add(new_link)
            new_urls.remove(a)
    return new_urls


def start_crawling(site_id, queue_set, delay, driver, threadName):
    if not queue_set:
        return
    url = queue_set.pop()
    print("checking url : ", threadName, " ", url)
    crawling_page = SeleniumHelper(url, driver)
    page_hash = hashlib.sha256(crawling_page.text.encode('utf-8')).hexdigest()

    # check if page hash already exists
    cur = conn.cursor()
    if is_page_alread_saved(url, cur):
        return

    sql = "SELECT id FROM crawldb.page where hash = %s"

    cur.execute(sql, (page_hash,))
    record_exists = cur.fetchone()

    if not record_exists:
        # check if html page
        if 'html' in crawling_page.content_type:
            cur.execute(
                "INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s) RETURNING id",
                (site_id, 'HTML', url, crawling_page.text, crawling_page.status_code, page_hash))
            page_id = cur.fetchone()[0]
            cur.close()
        else:
            cur.execute(
                "INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, NULL, %s, CURRENT_TIMESTAMP, %s) RETURNING id",
                (site_id, 'BINARY', url, crawling_page.status_code, page_hash))
            page_id = cur.fetchone()
            cur.close()

        new_urls = search_page_urls_and_images(url, page_id, crawling_page)
        new_urls1 = add_new_domains_to_queue(url, new_urls)
        # wait after every search

        queue_set |= new_urls1
        # for new_url in new_urls:
    #     url_queue.put(new_url)
    time.sleep(delay)
    start_crawling(site_id, queue_set, delay, driver, threadName)


def is_content_file_url(link):
    for format in content_types:
        if link.upper().endswith(format):
            return format
    return False


def get_base_url(url):
    base_url_parser = urlparse(url)
    return base_url_parser.scheme + "://" + base_url_parser.netloc

def make_request(url):
    try:
        response = requests.get(url)
        time.sleep(5)
        return response.text
    except:
       return ""

def get_sitemap(url):
    sitemap_url = urljoin(url, '/sitemap.xml')
    return make_request(sitemap_url)


def get_robots(url):
    robots_url = urljoin(url, '/robots.txt')
    return make_request(robots_url)

# TODO save urls on the page to link table
# TODO check if url is already present in queue
def search_page_urls_and_images(url, page_id, crawling_page):
    urls = set()
    cur = conn.cursor()
    # all_links = soup.findAll('a')

    for link in crawling_page.links:
        # parsing_link = link.get_attribute("href")
        parsing_link = link
        if parsing_link == "" or parsing_link is None:
            continue
        combined_link = urljoin(url, parsing_link)
        parsed_href = urlparse(combined_link)

        is_content_url = is_content_file_url(combined_link)
        if is_content_url:
            cur.execute("""INSERT INTO crawldb.page_data (page_id, data_type_code) VALUES (%s, %s)""",
                        (page_id, is_content_url,))
        # from ParseResult get link to be searched if gov.si
        elif ('gov.si' in parsed_href.netloc):
            clean_link = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            urls.add(clean_link) if clean_link not in urls else urls

    # get all images
    for image in crawling_page.images:
        if image == "" or image is None:
            continue
        combined_link = urljoin(url, image)
        parsed_image = urlparse(combined_link)

        # some images started on "data*"
        if parsed_image.scheme in ['http', 'https', 'www', '']:
            clean_url = parsed_image.scheme + "://" + parsed_image.netloc + parsed_image.path

            try:
                filename = clean_url.split('/')[-1].split('.')[0]
                file_extension = clean_url.split('/')[-1].split('.')[1]

                cur.execute("INSERT INTO crawldb.image VALUES(DEFAULT, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
                            (page_id, filename, file_extension, "BINARY"))
            except:
                print("nima extentiona")
    cur.close()
    return urls


global conn
# connect to the db
conn = psycopg2.connect(
    host='localhost',
    database='crawldb',
    user='crawldb',
    password='admin'
)
conn.autocommit = True

initial_seed = ['https://www.gov.si/', 'http://evem.gov.si/', 'https://e-uprava.gov.si/',
                'https://www.e-prostor.gov.si/', 'https://www.gov.si/']


class MyThread(threading.Thread):
    def __init__(self, threadID, name, q):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.q = q
        self.active = True

    def run(self):
        print("Starting " + self.name)
        process_data(self, self.name, self.q)
        print("Exiting " + self.name)


def insert_into_site(url, robots_content, sitemap_content, cur):
    cur.execute("INSERT INTO crawldb.site VALUES(DEFAULT, %s, %s, %s) RETURNING id",
                (url, robots_content, sitemap_content))
    id = cur.fetchone()[0]
    return id


def add_site(url, cur):
    if url not in current_searched_websites and not is_site_in_db(url, cur):
        current_searched_websites.append(url)
        robots_content = get_robots(url)
        sitemap_content = get_sitemap(url)
        site_id = insert_into_site(url, robots_content, sitemap_content, cur)
        return site_id
    return False


def process_data(thread, threadName, q):
    cur = conn.cursor()
    while not exit_flag:
        driver = SeleniumHelper.init_driver()
        if not workQueue.empty():
            thread.active = True
            url = q.get()
            print("%s processing %s" % (threadName, url))
            site_id = add_site(url, cur)
            if site_id:
                start_crawling(site_id, {url}, 5, driver, threadName)
            current_searched_websites.remove(url)
        else:
            thread.active = False
        driver.close()
    cur.close()


delete_all_data()

exit_flag = 0
number_of_workers = 4
workQueue = Queue()
threads = []

# Fill the queue
for word in initial_seed:
    workQueue.put(word)
    already_visited_sites.add(word)

# Create new threads
for index in range(number_of_workers):
    thread = MyThread(index + 1, "Thread" + str(index), workQueue)
    thread.start()
    threads.append(thread)


def is_any_thread_active(threads):
    for t in threads:
        if t.active:
            return True
    return False


# Wait for queue to empty and all threads inactive
while not workQueue.empty() or is_any_thread_active(threads):
    pass

exit_flag = 1

for t in threads:
    t.join()
