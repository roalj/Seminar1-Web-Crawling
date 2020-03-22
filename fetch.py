import urllib.robotparser
from urllib.request import urlparse, urljoin
import requests
import psycopg2
from bs4 import BeautifulSoup
import re
from urllib3 import request


# cur.execute("SELECT * from crawldb.data_type")
#
# for r in cur.fetchall():
#     print({r[0]})
#
# cur.close()
# conn.close()

def add_site_to_db(base_url, robots_content, sitemap_content):
    cur = conn.cursor()

    sql = "SELECT id FROM crawldb.site where domain = %s"
    cur.execute(sql, (base_url,))
    record_exists = cur.fetchone()

    #add site if not yet exists
    if not record_exists:
        cur.execute("INSERT INTO crawldb.site VALUES(DEFAULT, %s, %s, %s) RETURNING id",
                    (base_url, robots_content, sitemap_content))
        id = cur.fetchone()[0]
    else:
        id = record_exists[0]

    cur.close()

    return id


def check_robots(url):
    base_url_parser = urlparse(url)

    base_url = base_url_parser.scheme + "://" + base_url_parser.netloc

    rp = urllib.robotparser.RobotFileParser()

    robots_url = urljoin(base_url, '/robots.txt')
    rp.set_url(robots_url)
    rp.read()

    # print(rp.site_maps())
    if rp is None:
        add_site_to_db(base_url, "", "")
    else:
        #TODO rp.site_maps() -> only available in pyhton 3.8, unable to install psycopg2 on pyhton 3.8 with windows
        soup = BeautifulSoup(requests.get(robots_url).content, 'html.parser')
        print(str(soup))
        add_site_to_db(base_url, str(soup), "")


def search_page_urls_and_images(url):
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

        clean_url = parsed_image.scheme + "://" + parsed_image.netloc + parsed_image.path

        filename = clean_url.split('/')[-1].split('.')[0]
        file_extension = clean_url.split('/')[-1].split('.')[1]

        cur.execute("INSERT INTO crawldb.image VALUES(DEFAULT, %s, %s, %s, %s, CURRENT_TIMESTAMP)",
                    (1, filename, file_extension, "BINARY"))

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

# urls = search_page_urls_and_images("https://www.24ur.com/")
#TODO -> dobimo ID, shrani stran v tabelo page
check_robots("https://www.gov.si/")
