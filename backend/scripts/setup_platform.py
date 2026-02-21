import sqlite3

conn = sqlite3.connect('C:/file analysier/rag-saas/backend/data/app.db')

# Check for Platform tenant
result = conn.execute("SELECT id, name, slug FROM tenants WHERE slug='platform'").fetchall()
if result:
    print(f"Platform tenant exists: {result}")
else:
    # Create Platform tenant
    import uuid
    tenant_id = str(uuid.uuid4())
    conn.execute("""
        INSERT INTO tenants (id, name, slug, is_active, max_documents, max_storage_mb, created_at, updated_at)
        VALUES (?, 'Platform', 'platform', 1, 1000, 10240, datetime('now'), datetime('now'))
    """, (tenant_id,))
    conn.commit()
    print(f"Created Platform tenant: {tenant_id}")

# Get the tenant ID
result = conn.execute("SELECT id FROM tenants WHERE slug='platform'").fetchone()
print(f"Platform tenant ID: {result[0]}")

conn.close()
