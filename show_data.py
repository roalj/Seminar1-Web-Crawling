import matplotlib.pyplot as plt
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='crawldb',
    user='crawldb',
    password='admin'
)
conn.autocommit = True
cur = conn.cursor()

def get_all_sites():
    sql = "SELECT * FROM crawldb.site"
    cur.execute(sql, )
    return cur.fetchall()

def calculate_number_of_pages(sites):
    sql = "SELECT COUNT(*) FROM crawldb.page where site_id = %s"
    site_counted = []
    for s in sites:
        cur.execute(sql, (s[0],))
        num_subpages = cur.fetchone()
        if num_subpages[0] > 10:
            site_counted.append((num_subpages[0], s[1]))

    return site_counted




y = []
z = []
size = []
fig_dims = (25, 10)
num_rows = 8

sites = get_all_sites()
site_counted = calculate_number_of_pages(sites)


for s in range(0, len(site_counted), num_rows):
    for j in range(num_rows):
        if s+j < len(site_counted):
            y.append(j)
            z.append(s+num_rows)
            a = site_counted[s+j][0]
            size.append(50 + a)
            print(s+num_rows)


fig, ax = plt.subplots(figsize=fig_dims)
ax.scatter(z, y, size)
ax.axes.get_xaxis().set_visible(False)
ax.axes.get_yaxis().set_visible(False)
fig.patch.set_visible(False)
ax.axis('off')

for i in range(0, len(site_counted), 1):
    ax.annotate(site_counted[i][1], (z[i], y[i]), (z[i]+0.2, y[i]))

cur.close()
plt.show()
