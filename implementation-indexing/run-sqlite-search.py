import time


import psycopg2

global conn
# connect to the db
conn = psycopg2.connect(
    host='localhost',
    database='postgres',
    user='postgres',
    password='admin'
)
conn.autocommit = True


def get_query(_words):
    words_query = ""
    for word in _words:
        words_query += "'"+word+"'"+ ","

    search_query = '(' + words_query[:-1] + ')'
    return "SELECT * FROM posting where word in " + search_query


def fetch_data(_words):
    sql = get_query(_words)
    cur.execute(sql,)
    record_exists = cur.fetchall()
    return record_exists

def query_group(_documents):
    group_by_documents = {}
    for x in _documents:
        word = x[0]
        document = x[1]
        count = x[2]
        indexes = x[3]
        if document in group_by_documents:
            group_by_documents[document].append({'indexes': indexes, 'count': count})
        else:
            group_by_documents[document] = [{'indexes': indexes, 'count': count}]
    return group_by_documents

def create_snippets(_grouped):
    snippets = {}
    for key, document in _grouped.items():
        used_index = []
        count = 0
        row = []
        for i_word in document:
            for index in i_word['indexes'].split(','):
                index = int(index)
                count += 1
                if index not in used_index:
                    row.append([neighbours for neighbours in range(index-2, index+3)])
                used_index.append(index)
        snippets[key] = {'index': row, 'count:': count}
    return snippets


input_query = "social services"
cur = conn.cursor()
start_time = time.time()
a = fetch_data(input_query.split(" "))#loop_over(search_query.split(" "))
grouped = query_group(a)
snippets = create_snippets(grouped)
for key, value in snippets.items():
    print(key, value)
print("--- %s seconds ---" % (time.time() - start_time))




1
#if __name__ == '__main__':
#    method = sys.argv[1]