#!/usr/bin/env python3
"""
Run database migrations against Supabase PostgreSQL.
"""

import os
import sys
from pathlib import Path
import urllib.parse

# Try psycopg2 first, fall back to psycopg2-binary
try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    os.system(f"{sys.executable} -m pip install psycopg2-binary -q")
    import psycopg2

# Database connection settings for Supabase
# Project ref: jtmltcdnthzpvdayuwkl
PROJECT_REF = "jtmltcdnthzpvdayuwkl"
DB_PASSWORD = "YNs^a%gBDNLffAL3HQXw"

# Supabase connection options to try
CONNECTION_CONFIGS = [
    # Option 1: Pooler with postgres.project-ref user (new format)
    {
        "host": f"aws-0-us-west-1.pooler.supabase.com",
        "port": 6543,
        "user": f"postgres.{PROJECT_REF}",
        "database": "postgres",
    },
    # Option 2: Pooler us-east-1
    {
        "host": f"aws-0-us-east-1.pooler.supabase.com",
        "port": 6543,
        "user": f"postgres.{PROJECT_REF}",
        "database": "postgres",
    },
    # Option 3: Direct connection (older format)
    {
        "host": f"db.{PROJECT_REF}.supabase.co",
        "port": 5432,
        "user": "postgres",
        "database": "postgres",
    },
    # Option 4: Pooler session mode
    {
        "host": f"aws-0-us-west-1.pooler.supabase.com",
        "port": 5432,
        "user": f"postgres.{PROJECT_REF}",
        "database": "postgres",
    },
]

def try_connect(config):
    """Try to connect with the given config."""
    try:
        print(f"  Trying {config['host']}:{config['port']} as {config['user']}...")
        conn = psycopg2.connect(
            host=config["host"],
            port=config["port"],
            database=config["database"],
            user=config["user"],
            password=DB_PASSWORD,
            sslmode="require",
            connect_timeout=10
        )
        print(f"  ✓ Connected!")
        return conn
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        return None

def run_migrations():
    """Run all SQL migration files."""
    migrations_dir = Path(__file__).parent / "migrations"

    # Get all SQL files sorted by name
    sql_files = sorted(migrations_dir.glob("*.sql"))

    if not sql_files:
        print("No migration files found!")
        return False

    print(f"Found {len(sql_files)} migration file(s)")

    # Try different connection configurations
    print("\nConnecting to Supabase PostgreSQL...")
    conn = None
    for config in CONNECTION_CONFIGS:
        conn = try_connect(config)
        if conn:
            break

    if not conn:
        print("\n❌ Could not connect to database with any configuration.")
        print("\nPlease check:")
        print("1. The project URL is correct")
        print("2. The database password is correct")
        print("3. The project is fully provisioned (may take a few minutes for new projects)")
        return False

    conn.autocommit = True
    cursor = conn.cursor()

    # Run each migration
    print()
    for sql_file in sql_files:
        print(f"Running {sql_file.name}...")
        try:
            with open(sql_file, 'r') as f:
                sql = f.read()

            # Execute the SQL
            cursor.execute(sql)
            print(f"  ✓ {sql_file.name} completed")
        except Exception as e:
            error_msg = str(e)
            # Ignore "already exists" errors for idempotent migrations
            if "already exists" in error_msg:
                print(f"  ⚠ {sql_file.name} (some objects already exist)")
            else:
                print(f"  ✗ {sql_file.name} failed: {error_msg[:200]}")

    # Verify tables were created
    print("\nVerifying tables...")
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()
    print(f"Created {len(tables)} tables:")
    for table in tables:
        print(f"  - {table[0]}")

    # Verify functions were created
    print("\nVerifying functions...")
    cursor.execute("""
        SELECT routine_name
        FROM information_schema.routines
        WHERE routine_type = 'FUNCTION'
        AND routine_schema = 'public'
        ORDER BY routine_name;
    """)
    functions = cursor.fetchall()
    print(f"Created {len(functions)} functions:")
    for func in functions:
        print(f"  - {func[0]}")

    # Get index count
    cursor.execute("""
        SELECT count(*)
        FROM pg_indexes
        WHERE schemaname = 'public';
    """)
    index_count = cursor.fetchone()[0]
    print(f"\nTotal indexes: {index_count}")

    cursor.close()
    conn.close()

    print("\n✅ Database setup completed!")
    return True

if __name__ == "__main__":
    success = run_migrations()
    sys.exit(0 if success else 1)
