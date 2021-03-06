from collections import defaultdict

from bs4 import BeautifulSoup
from nltk import word_tokenize
import nltk
import re
from stopwords import *
import os
import sqlite3

nltk.download('punkt')


def create_db():
    c = conn.cursor()

    c.execute("DROP TABLE IF EXISTS IndexWord")
    c.execute("DROP TABLE IF EXISTS Posting")

    c.execute("""
        CREATE TABLE IndexWord (
          word TEXT PRIMARY KEY
        );
        """)

    c.execute("""        
        CREATE TABLE Posting (
          word TEXT NOT NULL,
          documentName TEXT NOT NULL,
          frequency INTEGER NOT NULL,
          indexes TEXT NOT NULL,
          PRIMARY KEY(word, documentName),
          FOREIGN KEY (word) REFERENCES IndexWord(word)
        );""")
    c.close()


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
def process(text, web_page):
    tokens = tokenize(text)
    already_processed = []
    for token in tokens:
        if token not in already_processed:
            word = Word(token, web_page, tokens.count(token),
                        [i for i in range(len(text_only)) if text_only.startswith(token, i)])
            already_processed.append(token)
            save_data_to_db(word)


def word_already_exists(word, cur):
    sql = "SELECT * FROM IndexWord where word = ?"
    cur.execute(sql, (word,))
    record_exists = cur.fetchone()
    return record_exists


def save_data_to_db(word_object):
    cur = conn.cursor()
    if not word_already_exists(word_object.word, cur):
        cur.execute("INSERT INTO IndexWord values (?);", (word_object.word,))

    cur.execute("INSERT INTO Posting (word, documentName, frequency, indexes) VALUES (?,?,?,?)",
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
conn = sqlite3.connect('inverted-index.db')
conn.isolation_level = None


create_db()

#
for web_site in os.listdir('../input-indexing'):
    for file in os.listdir('../input-indexing/' + web_site):
        if file.endswith('.html'):
            html_page = open('../input-indexing/' + web_site + '/' + file, 'r',
                        encoding='utf8').read()
            soup = BeautifulSoup(html_page, 'html.parser').findAll('body')[0]
            remove_non_text_elements(soup)
            text_only = soup.get_text().lower()
            process(text_only, web_site + '/' + file)