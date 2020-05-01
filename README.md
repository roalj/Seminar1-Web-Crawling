# Data Extraction
Extract data from 3 different websites using 3 different methods:
* Regular expressions (A)
* Xpath (B)
* Automatic data extraction (C)

##Installation
Python 3.6

To be able to run this project you need following packages:
* re
* lxml
* json
* bs4
* difflib
* sys

After packages are installed you can run the script using this command:
python run-extraction.py (A/B/C)

A, B or C represents the method that you want to use to retrieve data
# Fetcher

"Fetcher" is a web crawler used to crawl gov.si domains. We are sending requests based on robots.txt file or every 5 seconds if the crawl_delay in not defined. The project also contains python script that renders an image based on database with the scheme that is attached to the project (/db/init-scripts/crawldb.sql)

## Installation

Python 3.7

To be able to run this project you need following Python packages:  
* time
* queue
* urllib.request (urlparse, urljoin)
* requests
* psycopg2
* hashlib
* threading
* urllib.robotparser

For image rendering:
* matplotlib.pyplot
* math


To run the script, you need packages listed above. To change the number of threads you change line 342 in fetch.py to desired number.

DB backup link available in baza_drive.txt