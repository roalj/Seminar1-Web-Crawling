import time
from stopwords import *
from nltk import word_tokenize
import nltk
from bs4 import BeautifulSoup
import sqlite3
import sys

global conn

nltk.download('punkt')
OFF_SET_NEIGHBOUR = 20


def remove_non_text_elements(soup):
    for script in soup(["script", "style", "link", "iframe", "noscript"]):
        script.decompose()


def tokenize(text):
    tokens = []
    for word in word_tokenize(text.lower()):
        if word not in stop_words_slovene:
            tokens.append(word)
    return tokens


def word_already_exists(word, cur):
    sql = "SELECT * FROM IndexWord where word = ?"
    cur.execute(sql, (word,))
    record_exists = cur.fetchone()
    return record_exists


def save_data_to_db(word_object):
    cur = conn.cursor()
    if not word_already_exists(word_object.word, cur):
        cur.execute("INSERT INTO IndexWord values (%s);", (word_object.word,))

    cur.execute("INSERT INTO Posting (word, documentName, frequency, indexes) VALUES (?,?,?,?)",
                (
                    word_object.word, word_object.document, word_object.frequency,
                    ','.join(map(str, word_object.indexes))))
    cur.close()


class Word:
    def __init__(self, word, document, frequency, indexes):
        self.word = word
        self.document = document
        self.frequency = frequency
        self.indexes = indexes


# connect to the db
conn = sqlite3.connect('inverted-index.db')
conn.isolation_level = None


def get_query(_words):
    words_query = ""
    for word in _words:
        words_query += "'" + word + "'" + ","

    search_query = '(' + words_query[:-1] + ')'
    return "SELECT * FROM posting where word in " + search_query


def fetch_data(_words):
    sql = get_query(_words)
    cur.execute(sql, )
    record_exists = cur.fetchall()
    return record_exists


class SearchResult:
    def __init__(self, frequency, document, indexes):
        self.frequency = frequency
        self.document = document
        self.indexes = indexes
        self.snippet = ""
        self.create_snippet()

    def __str__(self):
        return str(self.frequency) + '\t' + self.document + "\t" + self.snippet

    def __lt__(self, other):
        return self.frequency > other.frequency

    def create_snippet(self):
        _text = parse_to_text('../input-indexing/' + self.document)
        for start_index in self.indexes:
            start = start_index - OFF_SET_NEIGHBOUR
            end = start_index + OFF_SET_NEIGHBOUR
            if start < 0:
                start = 0
            elif end > len(_text):
                end = len(_text)
            self.snippet += '...' + _text[start:end] + '...'


def query_group(_documents):
    group_by_documents = {}
    for x in _documents:
        word = x[0]
        document = x[1]
        count = x[2]
        indexes = x[3]
        result = {'indexes': indexes, 'count': count, 'word': word}
        if document in group_by_documents:
            group_by_documents[document].append(result)
        else:
            group_by_documents[document] = [result]
    return group_by_documents


def is_word_already_contained(word_start, word_len, indexes):
    word_end = word_start + word_len
    for i in indexes:
        if i - OFF_SET_NEIGHBOUR < word_start and i + OFF_SET_NEIGHBOUR > word_end:
            return True
    return False


def create_snippet_indexes(_grouped):
    snippets = {}
    result = []
    for key, document in _grouped.items():
        used_index = []
        count = 0
        for i_word in document:
            word = i_word['word']
            for index in i_word['indexes'].split(','):
                index = int(index)
                count += 1
                if not is_word_already_contained(index, len(word), used_index):
                    used_index.append(index)
        snippets[key] = {'indexes': used_index, 'count:': count}
        result.append(SearchResult(count, key, used_index))
    return result


def remove_non_text_elements(soup):
    for script in soup(["script", "style", "link", "iframe", "noscript"]):
        script.decompose()


def parse_to_text(file_path):
    html_page = open(file_path, 'r',
                     encoding='utf8').read()
    soup = BeautifulSoup(html_page, 'html.parser').findAll('body')[0]
    remove_non_text_elements(soup)
    return soup.get_text().lower()


if __name__ == '__main__':
    input_query = sys.argv[1]

    cur = conn.cursor()
    start_time = time.time()  # začetni čas
    a = fetch_data(tokenize(input_query))  # loop_over(search_query.split(" "))
    grouped = query_group(a)
    result = create_snippet_indexes(grouped)
    end_time = (time.time() - start_time)  # končni čas

    print("Results for a query:" + input_query)
    print("\t Results found in ", end_time)
    print('{:<15s}{:<50s}{:<200}'.format('Frequenices', 'Document', 'Snippet'))
    print('{:<15s}{:<50s}{:<200}'.format('-' * 13, '-' * 48, '-' * 100))
    result.sort()
    i = 0
    for r in result:
        i += 1
        if i > 6:
            break
        print('{:<15s}{:<50s}{:<1000}'.format(str(r.frequency), r.document,
                                              r.snippet.replace('\n', ' ').replace('\r', '')))

    1
