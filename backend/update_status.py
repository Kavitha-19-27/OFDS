import sqlite3

conn = sqlite3.connect('./data/app.db')
c = conn.cursor()
c.execute("UPDATE documents SET status = LOWER(status)")
conn.commit()
print(f'Updated {c.rowcount} documents')
c.execute('SELECT status, COUNT(*) FROM documents GROUP BY status')
print('Status counts:', dict(c.fetchall()))
conn.close()
