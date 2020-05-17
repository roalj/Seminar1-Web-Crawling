from collections import defaultdict

import psycopg2
from bs4 import BeautifulSoup
from nltk import word_tokenize
import nltk
import re
from stopwords import *

nltk.download('punkt')


def clear_db():
    cur = conn.cursor()
    cur.execute('DELETE FROM posting')
    cur.execute('DELETE FROM IndexWord ')
    cur.close()


def remove_non_text_elements(soup):
    for script in soup(["script", "style", "link", "iframe", "noscript"]):
        script.decompose()


def tokenize(text):
    tokens = []
    for word in word_tokenize(text):
        if word not in stop_words_slovene:
            tokens.append(word)
    return tokens


# A index v HTML dokemtnu al samo v tekstu?
def process(text):
    tokens = tokenize(text)
    already_processed = []
    for token in tokens:
        if token not in already_processed:
            word = Word(token, 'docName', tokens.count(token),
                        [i for i in range(len(text_only)) if text_only.startswith(token, i)])
            already_processed.append(token)
            save_data_to_db(word)


def word_already_exists(word, cur):
    sql = "SELECT * FROM IndexWord where word = %s"
    cur.execute(sql, (word,))
    record_exists = cur.fetchone()
    return record_exists


def save_data_to_db(word_object):
    cur = conn.cursor()
    if not word_already_exists(word_object.word, cur):
        cur.execute("INSERT INTO IndexWord values (%s);", (word_object.word,))

    cur.execute("INSERT INTO Posting (word, documentName, frequency, indexes) VALUES (%s,%s,%s,%s)",
                (
                word_object.word, word_object.document, word_object.frequency, ','.join(map(str, word_object.indexes))))
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
clear_db()

rtv1 = open('../input-indexing/podatki.gov.si/podatki.gov.si.1.html', 'r',
            encoding='utf8').read()

soup = BeautifulSoup(rtv1, 'html.parser').findAll('body')[0]
remove_non_text_elements(soup)
text_only = soup.get_text().lower()
process(text_only)
