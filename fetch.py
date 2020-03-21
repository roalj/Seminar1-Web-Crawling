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

def search_page(url):
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    urls = set()

    #get all links
    for link in soup.findAll('a'):
        parsing_link = link.get('href')

        if (parsing_link == "" or parsing_link is None):
            continue

        combined_link = urljoin(url, parsing_link)
        parsed_href = urlparse(combined_link)

        # from ParseResult get link to be searched if gov.si
        if ('gov.si' in parsed_href.netloc):
            clean_link = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            urls.add(combined_link) if combined_link not in urls else urls

    #get all images
    for image in soup.findAll('img'):

        image_source = image.get('src')

        if (image_source == "" or image_source is None):
            continue

        combined_link = urljoin(url, image_source)
        parsed_image = urlparse(combined_link)

        clean_url = parsed_image.scheme + "://" + parsed_image.netloc + parsed_image.path

        filename = clean_url.split('/')[-1].split('.')[0]
        file_extension = clean_url.split('/')[-1].split('.')[1]




    return urls


def open_db_connection(host, db, user, password):
    global conn
    # connect to the db
    conn = psycopg2.connect(
        host='localhost',
        database='crawler',
        user='postgres',
        password='admin'
    )

    conn.autocommit = True


urls = search_page("https://www.24ur.com/")
# for links in urls:
#     print(links)
