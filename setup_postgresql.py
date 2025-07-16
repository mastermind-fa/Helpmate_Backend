#!/usr/bin/env python3
"""
PostgreSQL Setup Script for HelpMate
This script sets up PostgreSQL tables using SQLAlchemy models (no data migration).
"""

import os
import sys
import asyncio
from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base

# Supabase PostgreSQL connection details
SUPABASE_URL = "postgresql://postgres.ffykytihaaafystofpli:s%24rsj%24k74Ytz-rA@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def check_postgresql_connection():
    """Check if PostgreSQL connection to Supabase is working"""
    try:
        import psycopg2
        conn = psycopg2.connect(SUPABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        print("✅ PostgreSQL connection to Supabase successful")
        print(f"   Database version: {version[0]}")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def create_tables():
    """Create all tables using SQLAlchemy"""
    try:
        os.environ['DATABASE_URL'] = SUPABASE_URL
        engine = create_engine(SUPABASE_URL)
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully in Supabase (no data migrated)")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def main():
    print("🚀 HelpMate Supabase PostgreSQL Table Setup Script")
    print("=" * 55)
    print("\n1. Checking PostgreSQL connection to Supabase...")
    if not check_postgresql_connection():
        return
    print("\n2. Creating tables in Supabase (no data migration)...")
    if not create_tables():
        return
    print("\n🎉 Table setup completed successfully!")
    print("\n📝 Next steps:")
    print("1. Use your API endpoints or curl scripts to add new data.")
    print("2. Your database is clean and ready for new data.")

if __name__ == "__main__":
    main() 