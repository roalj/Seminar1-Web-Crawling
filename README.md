# Data Indexing
##Installation
Python 3.7

To be able to run this project you need following packages:
```python
import os
import time
from nltk import word_tokenize
import nltk
from bs4 import BeautifulSoup
import sqlite3
import sys
```
Create database for indexing: 
```sql
CREATE TABLE IndexWord (
  word TEXT PRIMARY KEY
);

CREATE TABLE Posting (
  word TEXT NOT NULL,
  documentName TEXT NOT NULL,
  frequency INTEGER NOT NULL,
  indexes TEXT NOT NULL,
  PRIMARY KEY(word, documentName),
  FOREIGN KEY (word) REFERENCES IndexWord(word)
);
```
Then run the following script to fill the database with data
```bash
inverted-index.py
```

Then you can search for word(s) from the above generated database:
```bash
run-sqlite-search.py "SEARCH_PARAM"
```

or you can search it directly from files by:
```bash
run-basic-search.py "SEARCH_PARAM"
```


# Data Extraction
Extract data from 3 different websites using 3 different methods:
* Regular expressions (A)
* Xpath (B)
* Automatic data extraction (C)

##Installation
Python 3.6

To be able to run this project you need following packages:
```python
import re
from lxml import html
import json
from bs4 import BeautifulSoup
import difflib
import sys
```

After packages are installed you can run the script using this command:
```bash
python run-extraction.py (A/B/C)
```

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