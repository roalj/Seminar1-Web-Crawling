from collections import defaultdict

from bs4 import BeautifulSoup
from nltk import word_tokenize
import nltk
from stopwords import *
import os
import time
import sys

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


# A index v HTML dokemtnu al samo v tekstu?
def process(text, web_page):
    tokens = tokenize(text)
    already_processed = []
    for token in tokens:
        if token not in already_processed:
            word = Word(token, web_page, tokens.count(token))
            already_processed.append(token)
            dict[token].append(word)


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


def parse_to_text(file_path):
    html_page = open(file_path, 'r',
                     encoding='utf8').read()
    soup = BeautifulSoup(html_page, 'html.parser').findAll('body')[0]
    remove_non_text_elements(soup)
    return soup.get_text().lower()


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
            for index in i_word['indexes']:
                index = int(index)
                count += 1
                if not is_word_already_contained(index, len(word), used_index):
                    used_index.append(index)
        snippets[key] = {'indexes': used_index, 'count:': count}
        result.append(SearchResult(count, key, used_index))
    return result


def parse_to_text(file_path):
    html_page = open('../input-indexing/' + file_path, 'r',
                     encoding='utf8').read()
    soup = BeautifulSoup(html_page, 'html.parser').findAll('body')[0]
    remove_non_text_elements(soup)
    return soup.get_text().lower()


def query_group(_documents):
    group_by_documents = {}
    for x in _documents:
        word = x.word
        document = x.document
        count: object = x.frequency
        text = parse_to_text(document)

        indexes = [i for i in range(len(text)) if text.startswith(word, i)]

        result = {'indexes': indexes, 'count': count, 'word': word}
        if document in group_by_documents:
            group_by_documents[document].append(result)
        else:
            group_by_documents[document] = [result]
    return group_by_documents


class Word:
    def __init__(self, word, document, frequency):
        self.word = word
        self.document = document
        self.frequency = frequency


if __name__ == '__main__':
    input_query = sys.argv[1]

    start_time = time.time()  # začetni čas
    dict = defaultdict(list)
    for web_site in os.listdir('../input-indexing'):
        for file in os.listdir('../input-indexing/' + web_site):
            if file.endswith('.html'):
                html_page = open('../input-indexing/' + web_site + '/' + file, 'r',
                                 encoding='utf8').read()
                soup = BeautifulSoup(html_page, 'html.parser').findAll('body')[0]
                remove_non_text_elements(soup)
                text_only = soup.get_text().lower()
                process(text_only, web_site + '/' + file)

    end_time = (time.time() - start_time)  # končni čas

    input_tokens = tokenize(input_query)
    a = []
    for input_token in input_tokens:
        a.append(dict[input_token])

    joinedList = []
    for words in a:
        joinedList += words

    grouped = query_group(joinedList)
    result = create_snippet_indexes(grouped)
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
        print('{:<15s}{:<50s}{:<200}'.format(str(r.frequency), r.document,
                                             r.snippet.replace('\n', ' ').replace('\r', '')))
