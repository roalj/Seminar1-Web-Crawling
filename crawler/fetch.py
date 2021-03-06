import time
from queue import Queue
from urllib.request import urlparse, urljoin
import requests
import psycopg2
import hashlib
import threading
import urllib.robotparser

from bs4 import BeautifulSoup

lock = threading.Lock()
url_queue = Queue()
already_visited_sites = set()
already_visited_pages = set()
content_types = ['PDF', 'DOC', 'DOCX', 'PPT', 'PPTX']
current_searched_websites = []
headers = {'user-agent': 'fri-ieps-roalj'}


def is_site_in_db(base_url, cur):
    sql = "SELECT id FROM crawldb.site where domain = %s or domain = %s"
    cur.execute(sql, (base_url, change_to_http(base_url),))
    record_exists = cur.fetchone()
    return record_exists


# test
def delete_all_data():
    cur = conn.cursor()
    cur.execute("DELETE FROM crawldb.link")
    cur.execute("DELETE FROM crawldb.image")
    cur.execute("DELETE FROM crawldb.page_data")
    cur.execute("DELETE FROM crawldb.page")
    cur.execute("DELETE FROM crawldb.site")
    cur.close


def is_page_alread_saved(url, cur):
    with lock:
        sql = "SELECT id FROM crawldb.page where url = %s or url = %s"
        cur.execute(sql, (url, change_to_http(url),))
        record_exists = cur.fetchone()
        return record_exists


def add_new_domains_to_queue(url, new_urls, page_id):
    base_url = get_base_url(url)
    sub_domain_urls = set()
    for a in new_urls.copy():
        if not a.startswith(base_url):
            new_link = get_base_url(a)
            if new_link not in already_visited_sites:
                workQueue.put(Page(new_link, page_id))
                already_visited_sites.add(new_link)
            new_urls.remove(a)
        else:
            if a not in already_visited_pages:
                sub_domain_urls.add(a)

    return sub_domain_urls


def calculate_delay(time_passed, delay):
    if time_passed > delay:
        return 0
    return delay - time_passed

def is_site_disallowed(robot_rules, url):
    return robot_rules is not None and not robot_rules.can_fetch('*', url)


def site_contains_http_twice(url):
    return url.count('http') > 1


def start_crawling(site_id, queue_set, delay, threadName, robot_rules):
    if not queue_set:
        return
    while not queue_set.empty():
        page = queue_set.get(block=False)
        url = page.url
        start_time = time.time()
        print("checking url : ", threadName, " ", url)
        cur = conn.cursor()

        if is_page_alread_saved(url, cur) or is_site_disallowed(robot_rules, url) or site_contains_http_twice(url):
            print("--- %s seconds, thread name NONE: %s ---" % (time.time() - start_time, threadName))
            continue
            # start_crawling(site_id, queue_set, delay, threadName, robot_rules)
            # cur.close()
            # return

        try:
            # crawling_page = SeleniumHelper(url, threadName)
            request = requests.get(url, headers=headers)
            time.sleep(5)
            soup = BeautifulSoup(request.content, 'html.parser')
        except Exception as e:
            print("failed selenium: ", e)
            continue
            # start_crawling(site_id, queue_set, delay, threadName, robot_rules)
            # cur.close()
            # return


        sql = "SELECT id FROM crawldb.page where hash = %s"
        page_hash = hashlib.sha256(soup.text.encode('utf-8')).hexdigest()
        cur.execute(sql, (page_hash,))
        record_exists = cur.fetchone()

        if not record_exists:
            # check if html page
            if 'html' in request.headers['Content-Type']:
                with lock:
                    cur.execute(
                        "INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP, %s) RETURNING id",
                        (site_id, 'HTML', url, request.text if request.text != '' else 'NULL', request.status_code, page_hash))
                    page_id = cur.fetchone()[0]
            else:
                with lock:
                    cur.execute(
                        "INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, NULL, %s, CURRENT_TIMESTAMP, %s) RETURNING id",
                        (site_id, 'BINARY', url, request.status_code, page_hash))
                    page_id = cur.fetchone()[0]

            if page.source_page_id is not None:
                print("link from: " + str(page.source_page_id) + " , to: " + str(page_id))
                with lock:
                    cur.execute(
                        "INSERT INTO crawldb.link VALUES(%s, %s)",
                        (page.source_page_id, page_id)
                    )
        else:
            with lock:
                cur.execute(
                    "INSERT INTO crawldb.page VALUES(DEFAULT, %s, %s, %s, NULL , %s, CURRENT_TIMESTAMP, %s) RETURNING id",
                    (site_id, 'DUPLICATE', url, request.status_code, page_hash))
                page_id = cur.fetchone()[0]
            continue

        cur.close()

        already_visited_pages.add(url)

        new_urls = search_page_urls_and_images(url, page_id, soup)
        sub_domain_urls = add_new_domains_to_queue(url, new_urls, page_id)

        new_pages = set()
        for new_url in sub_domain_urls:
            queue_set.put(Page(new_url, page_id))

        # queue_set |= new_pages

        current_delay = calculate_delay(time.time() - start_time, delay)
        print("current_delay ", current_delay)
        time.sleep(current_delay)
        print("--- %s seconds, thread name: %s ---" % (time.time() - start_time, threadName))
        # start_crawling(site_id, queue_set, delay, threadName, robot_rules)


def is_content_file_url(link):
    for format in content_types:
        if link.upper().endswith(format):
            return format
    return False


def change_to_http(url):
    if url.startswith('https://'):
        return url.replace('https://', 'http://', 1)
    else:
        return url


def get_base_url(url):
    base_url_parser = urlparse(url)
    return base_url_parser.scheme + "://" + base_url_parser.netloc


def make_request(url):
    try:
        response = requests.get(url, headers=headers)
        time.sleep(5)
        if response.status_code < 400:
            return response.text
        else:
            return ""
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
def search_page_urls_and_images(url, page_id, soup):
    urls = set()
    cur = conn.cursor()
    # all_links = soup.findAll('a')

    for link in soup.findAll('a'):
        parsing_link = link.get('href')
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
    for image in soup.findAll('img'):
        image_source = image.get('src')
        if image_source == "" or image_source is None:
            continue
        combined_link = urljoin(url, image_source)
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
    database='crawler',
    user='postgres',
    password='admin'
)
conn.autocommit = True

initial_seed = ['https://www.gov.si/', 'http://evem.gov.si/', 'https://e-uprava.gov.si/',
                'https://www.e-prostor.gov.si/']


class Page:
    def __init__(self, url, source_page_id):
        self.url = url
        self.source_page_id = source_page_id


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

        if robots_content == "":
            return [site_id, 5, None]
        else:
            rp = urllib.robotparser.RobotFileParser()
            robots_url = urljoin(url, '/robots.txt')
            rp.set_url(robots_url)
            rp.read()
            if rp is None:
                return [site_id, 5, None]
            else:
                if rp.crawl_delay("*") is None:
                    return [site_id, 5, rp]
                else:
                    return [site_id, rp.crawl_delay("*"), rp]
    return False


def process_data(thread, threadName, q):
    cur = conn.cursor()
    while not exit_flag:
        if not workQueue.empty():
            thread.active = True
            page = q.get()
            url = page.url
            print("%s processing %s" % (threadName, url))
            site_id = add_site(url, cur)
            queue = Queue()
            queue.put(page)
            if site_id:
                # current_searched_websites.remove(url)
                print(site_id[0])
                start_crawling(site_id[0], queue, site_id[1], threadName, site_id[2])
                current_searched_websites.remove(url)
        else:
            thread.active = False
    #  driver.close()
    cur.close()


delete_all_data()

exit_flag = 0
number_of_workers = 30
workQueue = Queue()
threads = []

# Fill the queue
for word in initial_seed:
    workQueue.put(Page(word, None))
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
