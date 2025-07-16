import psycopg2
import os

# Use the Transaction Pooler connection string
conn_str = "postgresql://postgres.ffykytihaaafystofpli:s%24rsj%24k74Ytz-rA@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

try:
    print("Connecting to:", conn_str)
    conn = psycopg2.connect(conn_str)
    cur = conn.cursor()
    cur.execute("SELECT version();")
    version = cur.fetchone()
    print("✅ Connection successful! Postgres version:", version[0])
    cur.close()
    conn.close()
except Exception as e:
    print("❌ Connection failed:", e) 