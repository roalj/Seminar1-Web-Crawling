import time
import urllib.robotparser
from queue import Queue
from urllib.request import urlparse, urljoin
import requests
import psycopg2
from bs4 import BeautifulSoup
import hashlib
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

import re

from db.SeleniumHelper import SeleniumHelper

test_links = ['https://www.e-prostor.gov.si/', 'https://www.e-prostor.gov.si/', 'https://www.e-prostor.gov.si/o-portalu/', 'https://www.e-prostor.gov.si/kontakt/', 'https://www.e-prostor.gov.si/access-to-geodetic-data/ordering-data/', 'https://www.e-prostor.gov.si/o-portalu/', 'https://www.e-prostor.gov.si/kontakt/', 'https://www.e-prostor.gov.si/access-to-geodetic-data/ordering-data/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/zbirka-vrednotenja-nepremicnin/', 'https://www.e-prostor.gov.si/dostop-do-podatkov/dostop-do-podatkov/', 'https://www.e-prostor.gov.si/brezplacni-podatki/', 'https://www.e-prostor.gov.si/metapodatki/', 'https://www.e-prostor.gov.si/aplikacije/', 'https://www.e-prostor.gov.si/izobrazevanja/izobrazevanje-geodetov-po-zgeod-1/', 'https://www.e-prostor.gov.si/informacije/', 'https://www.e-prostor.gov.si/#', 'https://eprostor.sigov.si/pgp/index.jsp', 'https://gis.gov.si/ezkn/', 'http://prostor3.gov.si/zem_imena/zemImena.jsp', 'http://sitranet.si/sivis.html', 'http://sitranet.si/sitrik.html', 'http://www.e-prostor.gov.si/fileadmin/DPKS/Transformacija_v_novi_KS/Aplikacije/3tra.zip', 'http://sitranet.si/', 'http://sitra.sitranet.si/', 'https://vprasalnik.gu.gov.si/DAZK/faces/Login.jspx', 'http://www.gis.si/ude/', 'https://www.mvn.e-prostor.gov.si/evidence/evidenca-trga-nepremicnin/porocanje-v-etn/', 'http://prostor3.gov.si/javni', 'http://prostor3.gov.si/ETN-JV/', 'http://prostor3.gov.si/preg/', 'http://prostor3.sigov.si/preg/', 'http://prostor3.gov.si/zvn/zvn/ZVN.html', 'https://egp.gu.gov.si/egp/', 'https://eprostor.sigov.si/pgp/index.jsp', 'https://gis.gov.si/ezkn/', 'http://prostor3.gov.si/zem_imena/zemImena.jsp', 'http://sitranet.si/sivis.html', 'http://sitranet.si/sitrik.html', 'http://www.e-prostor.gov.si/fileadmin/DPKS/Transformacija_v_novi_KS/Aplikacije/3tra.zip', 'http://sitranet.si/', 'http://sitra.sitranet.si/', 'https://vprasalnik.gu.gov.si/DAZK/faces/Login.jspx', 'http://www.gis.si/ude/', 'https://www.mvn.e-prostor.gov.si/evidence/evidenca-trga-nepremicnin/porocanje-v-etn/', 'http://prostor3.gov.si/javni', 'http://prostor3.gov.si/ETN-JV/', 'http://prostor3.gov.si/preg/', 'http://prostor3.sigov.si/preg/', 'http://prostor3.gov.si/zvn/zvn/ZVN.html', 'https://egp.gu.gov.si/egp/', 'https://eprostor.sigov.si/pgp/index.jsp', 'https://gis.gov.si/ezkn/', 'http://prostor3.gov.si/zem_imena/zemImena.jsp', 'http://sitranet.si/sivis.html', 'http://sitranet.si/sitrik.html', 'http://www.e-prostor.gov.si/fileadmin/DPKS/Transformacija_v_novi_KS/Aplikacije/3tra.zip', 'https://www.e-prostor.gov.si/aplikacije/', 'https://www.e-prostor.gov.si/aktualno/sprememba-v-predvidenih-podatkovnih-strukturah-ren-in-ev-po-01042020/', 'https://www.e-prostor.gov.si/fileadmin/Spletni_servisi/Obvestilo_uporabnikom_servisi_storitve_eprostor.pdf', 'https://www.e-prostor.gov.si/aktualno/preklic-uporabe-objavljenih-dokumentov-za-ks-in-ren/', 'https://www.e-prostor.gov.si/aktualno/sprememba-v-predvidenih-podatkovnih-strukturah-ren-in-ev-po-01042020/', 'https://www.e-prostor.gov.si/fileadmin/Spletni_servisi/Obvestilo_uporabnikom_servisi_storitve_eprostor.pdf', 'https://www.e-prostor.gov.si/aktualno/preklic-uporabe-objavljenih-dokumentov-za-ks-in-ren/', 'https://www.e-prostor.gov.si/aktualno/sprememba-v-predvidenih-podatkovnih-strukturah-ren-in-ev-po-01042020/', 'https://www.e-prostor.gov.si/aktualno-arhiv/', 'https://www.mvn.e-prostor.gov.si/', 'https://www.mvn.e-prostor.gov.si/', 'https://www.projekt.e-prostor.gov.si/', 'https://www.projekt.e-prostor.gov.si/', 'https://egp.gu.gov.si/egp/', 'http://www.izs.si/e-izobrazevanja/e-izobrazevanja/zemljiski-kataster/', 'https://www.e-prostor.gov.si/#tab1-952', 'https://www.e-prostor.gov.si/#tab2-952', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/topografski-in-kartografski-podatki/aerofotografije/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/topografski-in-kartografski-podatki/digitalni-model-visin/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/drzavni-prostorski-koordinatni-sistem/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/nepremicnine/drzavna-meja/', 'https://www.mvn.e-prostor.gov.si/evidence/evidenca-trga-nepremicnin/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/nepremicnine/kataster-stavb/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/topografski-in-kartografski-podatki/ortofoto/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/nepremicnine/register-nepremicnin/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/nepremicnine/register-prostorskih-enot/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/topografski-in-kartografski-podatki/register-zemljepisnih-imen/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/topografski-in-kartografski-podatki/topografski-podatki-in-karte/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/zbirka-vrednotenja-nepremicnin/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/zbirni-kataster-gospodarske-javne-infrastrukture/', 'https://www.e-prostor.gov.si/zbirke-prostorskih-podatkov/nepremicnine/zemljiski-kataster/', 'https://www.e-prostor.gov.si/dostop-do-podatkov/dostop-do-podatkov/', 'https://www.e-prostor.gov.si/dostop-do-podatkov/dostop-do-podatkov/#tab3-1029', 'https://www.e-prostor.gov.si/fileadmin/narocanje/obr_za_narocilo.doc', 'https://www.e-prostor.gov.si/dostop-do-podatkov/dostop-do-podatkov/mapa/vzorci-podatkov/', 'https://www.e-prostor.gov.si/brezplacni-podatki/', 'https://www.e-prostor.gov.si/informacije/vsa-pogosta-vprasanja/?no_cache=1', 'https://www.gov.si/drzavni-organi/organi-v-sestavi/geodetska-uprava/', 'https://www.mvn.e-prostor.gov.si/', 'https://www.projekt.e-prostor.gov.si/', 'http://e-uprava.gov.si/', 'http://arsq.gov.si/Query/detail.aspx?id=23253', 'http://www.dlib.si/v2/Results.aspx?query=source%3dzemljevidi%2bAND%2brele%3dZemljevidi&browse=zemljevidi&pageSize=20&sort=date&sortDir=ASC', 'http://www.zveza-geodetov.si/', 'http://www.geoportal.gov.si/', 'https://www.e-prostor.gov.si/pogoji-uporabe/', 'https://www.e-prostor.gov.si/varstvo-osebnih-podatkov-in-uporaba-informacij-javnega-znacaja/', 'https://www.e-prostor.gov.si/kolofon/', 'https://www.e-prostor.gov.si/piskotki/', 'https://www.e-prostor.gov.si/dostopnost/', 'mailto:pisarna.gu@gov.si?subject=Kontakt%20o%20dostopnosti', 'https://www.e-prostor.gov.si/piskotki/']

url_queue = Queue()
already_visited_sites = []
content_types = ['PDF', 'DOC', 'DOCX', 'PPT', 'PPTX']

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
    crawling_page = SeleniumHelper(url, driver)
    #crawling_page = requests.get(url)
    page_hash = hashlib.sha256(crawling_page.text.encode('utf-8')).hexdigest()

    # check if page hash already exists
    cur = conn.cursor()
    sql = "SELECT id FROM crawldb.page where hash = %s"

    #cur.execute("DELETE FROM crawldb.image")
   # cur.execute("DELETE FROM crawldb.page_data")
   # cur.execute("DELETE FROM crawldb.page")

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

        # wait after every search
        time.sleep(delay)

        for new_url in new_urls:
            url_queue.put(new_url)

    search_next()

def is_content_file_url(link):
    for format in content_types:
        if link.upper().endswith(format):
            return format
    return False

def check_robots(url):
    base_url_parser = urlparse(url)

    base_url = base_url_parser.scheme + "://" + base_url_parser.netloc

    rp = urllib.robotparser.RobotFileParser()

    robots_url = urljoin(base_url, '/robots.txt')

    html = requests.get(robots_url)

    # wait 5 seconds
    time.sleep(5)

    # we don't want 404 to be stored in the db
    if html.status_code != 404:
        rp.set_url(robots_url)
        rp.read()

        if rp is None:
            id = add_site_to_db(base_url, "", "")
            start_crawling(id, url, 5)
        else:
            # TODO rp.site_maps() -> only available in pyhton 3.8, unable to install psycopg2 on pyhton 3.8 with windows
            id = add_site_to_db(base_url, html.content, "")
            if rp.crawl_delay("*") is None:
                start_crawling(id, url, 5)
            else:
                start_crawling(id, url, rp.crawl_delay("*"))
    else:
        id = add_site_to_db(base_url, "", "")
        start_crawling(id, url, 5)



"""def compare_links(all_links):
    new_all_links = []
    for link in all_links:
        parsing_link = link.get('href')
        new_all_links.append(parsing_link)

    for a in test_links:
        if a not in new_all_links:
            print(a)"""



# TODO save urls on the page to link table
# TODO check if url is already present in queue
def search_page_urls_and_images(url, page_id, crawling_page):
    #soup = BeautifulSoup(crawling_page.content, 'html.parser')
    urls = set()
    cur = conn.cursor()
    # get all links
    #all_links = soup.findAll('a')

    print("compare1")
    for link in crawling_page.links:
        parsing_link = link.get_attribute("href")

        if parsing_link == "" or parsing_link is None:
            continue
        combined_link = urljoin(url, parsing_link)
        parsed_href = urlparse(combined_link)


        is_content_url = is_content_file_url(combined_link)
        if is_content_url:
            cur.execute("""INSERT INTO crawldb.page_data (page_id, data_type_code) VALUES (%s, %s)""", (page_id, is_content_url,))
        # from ParseResult get link to be searched if gov.si
        elif ('gov.si' in parsed_href.netloc):
            clean_link = parsed_href.scheme + "://" + parsed_href.netloc + parsed_href.path
            urls.add(clean_link) if clean_link not in urls else urls

    #cur = conn.cursor()
    # get all images
    for image in crawling_page.images:
        image_source = image.get_attribute('src')

        if image_source == "" or image_source is None:
            continue

        combined_link = urljoin(url, image_source)
        parsed_image = urlparse(combined_link)

        # some images started on "data*"
        if parsed_image.scheme in ['http', 'https', 'www']:
            clean_url = parsed_image.scheme + "://" + parsed_image.netloc + parsed_image.path

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
    database='crawldb',
    user='crawldb',
    password='admin'
)
driver = SeleniumHelper.init_driver()
conn.autocommit = True

initial_seed = ['https://www.gov.si/', 'http://evem.gov.si/', 'https://e-uprava.gov.si/',
                'https://www.e-prostor.gov.si/', 'https://www.gov.si/']

"""initial_seed = ['https://www.e-prostor.gov.si/']"""

for initial_url in initial_seed:
    url_queue.put(initial_url)

search_next()
driver.close()