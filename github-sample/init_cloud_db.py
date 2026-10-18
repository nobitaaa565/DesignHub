#!/usr/bin/env python3
"""
Database Initialization Utility for DesignHub
Supports both Cloud PostgreSQL (via DATABASE_URL) and local SQLite.
"""
import os
import sys

def init():
    raw_db_url = os.environ.get("DATABASE_URL", "").strip()
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)

    if raw_db_url:
        try:
            import psycopg2
            print("🐘 Connecting to PostgreSQL at DATABASE_URL...")
            conn = psycopg2.connect(raw_db_url)
            c = conn.cursor()
            with open("schema_postgres.sql", "r", encoding="utf-8") as f:
                sql = f.read()
            c.execute(sql)
            conn.commit()
            conn.close()
            print("✅ Cloud PostgreSQL initialized successfully with all tables and seed data!")
            return
        except ImportError:
            print("⚠️ psycopg2 not installed. Run: pip install psycopg2-binary")
        except Exception as e:
            print(f"❌ PostgreSQL initialization error: {e}")

    # Fallback SQLite
    import sqlite3
    print("💾 Initializing local SQLite database (subscriptions.db)...")
    conn = sqlite3.connect("subscriptions.db")
    with open("schema_sqlite.sql", "r", encoding="utf-8") as f:
        sql = f.read()
    conn.executescript(sql)
    conn.close()
    print("✅ Local SQLite database initialized successfully!")

if __name__ == "__main__":
    init()
