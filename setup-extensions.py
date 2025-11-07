"""Script to create PostgreSQL extensions"""
import psycopg2
from app.config import settings
import sys

try:
    # Parse database URL
    db_url = settings.database_url
    if db_url.startswith('postgresql://'):
        # Extract connection details
        parts = db_url.replace('postgresql://', '').split('@')
        auth = parts[0].split(':')
        host_db = parts[1].split('/')
        host_port = host_db[0].split(':')
        
        user = auth[0]
        password = auth[1] if len(auth) > 1 else ''
        host = host_port[0]
        port = int(host_port[1]) if len(host_port) > 1 else 5432
        database = host_db[1] if len(host_db) > 1 else 'postgres'
        
        print(f"Connecting to database: {database}@{host}:{port}")
        
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        
        cur = conn.cursor()
        
        # Create extensions
        print("\nCreating extensions...")
        
        try:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            conn.commit()
            print("✓ uuid-ossp extension created")
        except Exception as e:
            print(f"⚠ uuid-ossp: {e}")
            conn.rollback()
        
        try:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
            conn.commit()
            print("✓ pg_trgm extension created")
        except Exception as e:
            print(f"⚠ pg_trgm: {e}")
            conn.rollback()
        
        try:
            cur.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
            conn.commit()
            print("✓ vector extension created")
        except Exception as e:
            print(f"⚠ vector extension not available (optional): {e}")
            conn.rollback()
        
        # Verify
        cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'vector')")
        extensions = cur.fetchall()
        print("\nInstalled extensions:")
        for ext in extensions:
            print(f"  - {ext[0]}: {ext[1]}")
        
        conn.close()
        print("\n✓ Extensions setup complete!")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
        
except Exception as e:
    print(f"Failed to connect to database: {e}")
    print("\nPlease ensure:")
    print("  1. PostgreSQL is running")
    print("  2. Database exists")
    print("  3. Connection details in .env are correct")
    sys.exit(1)

