import sqlite3

conn = sqlite3.connect('C:/file analysier/rag-saas/backend/data/app.db')

# Make admin@rag.com the single ADMIN
conn.execute("UPDATE users SET role='ADMIN' WHERE email='admin@rag.com'")

# Convert all other users to USER (including superadmin@rag.com)
conn.execute("UPDATE users SET role='USER' WHERE email != 'admin@rag.com'")

conn.commit()
print('Updated roles - only admin@rag.com is ADMIN')
result = conn.execute("SELECT email, role FROM users ORDER BY role DESC, email").fetchall()
for r in result:
    print(f"  {r[0]}: {r[1]}")
conn.close()
