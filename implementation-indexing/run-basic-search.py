from collections import defaultdict

import psycopg2
from bs4 import BeautifulSoup
from nltk import word_tokenize
import nltk
import re
from stopwords import *

nltk.download('punkt')


def remove_non_text_elements(soup):
    for script in soup(["script", "style", "link", "iframe", "noscript"]):
        script.decompose()


def save_to_db(word, document_name, frequency, indexes):
    cur = conn.cursor()
    cur.execute("INSERT INTO inverted-index.Posting (word, documentName, frequency, indexes) VALUES (?,?,?,?)",
                (word, document_name, frequency, indexes))
    cur.close()


class Word:
    def __init__(self, word, document, frequency, indexes):
        self.word = word
        self.document = document
        self.frequency = frequency
        self.indexes = indexes


global conn
# connect to the db
conn = psycopg2.connect(
    host='localhost',
    database='inverted-index',
    user='postgres',
    password='admin'
)
conn.autocommit = True

rtv1 = open('../input-indexing/podatki.gov.si/podatki.gov.si.1.html', 'r',
            encoding='utf8').read()

soup = BeautifulSoup(rtv1, 'html.parser').findAll('body')[0]
remove_non_text_elements(soup)
text_only = soup.get_text().lower()

tokens = []
for word in word_tokenize(text_only):
    if word not in stop_words_slovene:
        tokens.append(word)

dict_list = []

# A index v HTML dokemtnu al samo v tekstu?
for token in tokens:
    if not any(word.word == token for word in dict_list):
        dict_list.append(Word(token, 'docName', tokens.count(token), [i for i in range(len(text_only)) if text_only.startswith(token, i)]))


for word in dict_list:
    print(word.word)
