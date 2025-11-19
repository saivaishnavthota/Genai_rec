"""
Quick script to test PostgreSQL database connection
Run this to verify your database credentials before starting the server
"""
import sys
import os

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app.config import settings
    import psycopg2
    
    print("🔍 Testing database connection...")
    print(f"📋 Database URL: {settings.database_url.replace(settings.postgres_password, '***')}")
    print()
    
    # Parse connection details
    db_url = settings.database_url
    # Extract connection details
    if db_url.startswith("postgresql://"):
        parts = db_url.replace("postgresql://", "").split("@")
        if len(parts) == 2:
            user_pass = parts[0].split(":")
            host_db = parts[1].split("/")
            if len(host_db) == 2:
                host_port = host_db[0].split(":")
                
                user = user_pass[0] if len(user_pass) > 0 else "postgres"
                password = user_pass[1] if len(user_pass) > 1 else ""
                host = host_port[0] if len(host_port) > 0 else "localhost"
                port = host_port[1] if len(host_port) > 1 else "5432"
                database = host_db[1] if len(host_db) > 1 else "genai_hiring"
                
                print(f"📝 Connection details:")
                print(f"   User: {user}")
                print(f"   Host: {host}")
                print(f"   Port: {port}")
                print(f"   Database: {database}")
                print()
                
                try:
                    # Test connection
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        database=database,
                        user=user,
                        password=password
                    )
                    
                    print("✅ Database connection successful!")
                    print(f"   Connected to: {database}")
                    
                    # Check if database exists and get version
                    cur = conn.cursor()
                    cur.execute("SELECT version();")
                    version = cur.fetchone()
                    print(f"   PostgreSQL version: {version[0][:50]}...")
                    
                    cur.close()
                    conn.close()
                    print()
                    print("🎉 Database is ready to use!")
                    
                except psycopg2.OperationalError as e:
                    print("❌ Database connection failed!")
                    print()
                    print("Error details:")
                    print(f"   {str(e)}")
                    print()
                    print("💡 Solutions:")
                    print("   1. Check if PostgreSQL is running")
                    print("   2. Verify the password in .env file")
                    print("   3. Make sure the database 'genai_hiring' exists")
                    print("   4. Check if PostgreSQL is listening on port 5432")
                    print()
                    print("📚 See FIX_DATABASE_CONNECTION.md for detailed help")
                    sys.exit(1)
                    
                except psycopg2.Error as e:
                    print(f"❌ Database error: {e}")
                    sys.exit(1)
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're in the backend directory and dependencies are installed")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

