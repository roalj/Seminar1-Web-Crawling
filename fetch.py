import urllib.robotparser
from queue import Queue
from urllib.request import urlparse, urljoin
import requests
import psycopg2
from bs4 import BeautifulSoup
import hashlib
import re

# cur.execute("SELECT * from crawldb.data_type")
#
# for r in cur.fetchall():
#     print({r[0]})
#
# cur.close()
# conn.close()
url_queue = Queue()
already_visited_sites = []


def add_site_to_db(base_url, robots_content, sitemap_content):
    cur = conn.cursor()

    sql = "SELECT id FROM crawldb.site where domain = %s"
    cur.execute(sql, (base_url,))
    record_exists = cur.fetchone()

    # add site if not yet exists
    if not record_exists:
        cur.execute("INSERT INTO crawldb.site VALUES(DEFAULT, %s, %s, %s) RETURNING id",
                    (base_url, robots_content, sitemap_content))
        id = cur.fetchone()[0]
    else:
        id = record_exists[0]

    cur.close()

    return id


def start_crawling(site_id, url, delay):
    # print(site_id)
    # print(url)
    # print(delay)

    crawling_page = requests.get(url)
    page_hash = hashlib.sha256(crawling_page.text.encode('utf-8')).hexdigest()

    # check if page hash already exists
    cur = conn.cursor()
    sql = "SELECT id FROM crawldb.page where hash = %s"
    cur.execute(sql, (page_hash,))
    record_exists = cur.fetchone()

    if not record_exists:
        # check if html page
        if 'html' in crawling_page.headers['content-type']:
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

        new_urls = search_page_urls_and_images(url, page_id)

        for new_url in new_urls:
            url_queue.put(new_url)

    search_next()


def check_robots(url):
    base_url_parser = urlparse(url)

    base_url = base_url_parser.scheme + "://" + base_url_parser.netloc

    rp = urllib.robotparser.RobotFileParser()

    robots_url = urljoin(base_url, '/robots.txt')

    html = requests.get(robots_url)

    # we don't want 404 to be stored in the db
    if html.status_code != 404:
        rp.set_url(robots_url)
        rp.read()

        # print(rp.site_maps())
        if rp is None:
            id = add_site_to_db(base_url, "", "")
            start_crawling(id, url, 5)
        else:
            # TODO rp.site_maps() -> only available in pyhton 3.8, unable to install psycopg2 on pyhton 3.8 with windows
            soup = BeautifulSoup(requests.get(robots_url).content, 'html.parser')
            id = add_site_to_db(base_url, str(soup), "")
            if rp.crawl_delay("*") is None:
                start_crawling(id, url, 5)
            else:
                start_crawling(id, url, rp.crawl_delay("*"))
    else:
        id = add_site_to_db(base_url, "", "")
        start_crawling(id, url, 5)


# TODO save urls on the page to link table
# TODO check if url is already present in queue
def search_page_urls_and_images(url, page_id):
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    urls = set()

    # get all links
    for link in soup.findAll('a'):
        parsing_link = link.get('href')

        if parsing_link == "" or parsing_link is None:
            continue

        combined_link = urljoin(url, parsing_link)
        parsed_href = urlparse(combined_link)

        # from ParseResult get link to be searched if gov.si
        if ('gov.si' in parsed_href.netloc):
            clean_link = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            urls.add(combined_link) if combined_link not in urls else urls

    cur = conn.cursor()
    # get all images
    for image in soup.findAll('img'):

        image_source = image.get('src')

        if image_source == "" or image_source is None:
            continue

        combined_link = urljoin(url, image_source)
        parsed_image = urlparse(combined_link)

        # some images started on "data*"
        if parsed_image.scheme in ['http', 'https', 'www']:
            clean_url = parsed_image.scheme + "://" + parsed_image.netloc + parsed_image.path
            print(parsed_image.scheme)

            filename = clean_url.split('/')[-1].split('.')[0]
            file_extension = clean_url.split('/')[-1].split('.')[1]

            cur.execute("INSERT INTO crawldb.image VALUES(DEFAULT, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
                        (page_id, filename, file_extension, "BINARY"))

    cur.close()

    return urls


def search_next():
    if url_queue.empty():
        return

    url_to_be_searched = url_queue.get(block=True)

    if url_to_be_searched in already_visited_sites:
        search_next()
    else:
        already_visited_sites.append(url_to_be_searched)
        check_robots(url_to_be_searched)


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
                'https://www.e-prostor.gov.si/', 'https://www.gov.si/']

for initial_url in initial_seed:
    url_queue.put(initial_url)

search_next()
