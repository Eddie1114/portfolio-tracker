import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from app.core.config import settings
import re

def create_database():
    # Extract database name from URL
    match = re.match(r'postgresql://[^:]+:[^@]+@[^:]+(?::\d+)?/([^?]+)', settings.DATABASE_URL)
    if not match:
        raise ValueError("Invalid DATABASE_URL format")
    
    db_name = match.group(1)
    
    # Create connection string for postgres database
    conn_string = settings.DATABASE_URL.replace(db_name, "postgres")
    
    print(f"Creating database {db_name}...")
    
    try:
        # Connect to postgres database
        conn = psycopg2.connect(conn_string)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            print(f"✅ Database {db_name} created successfully!")
        else:
            print(f"ℹ️ Database {db_name} already exists.")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error creating database: {str(e)}")
        print("\nPlease make sure:")
        print("1. PostgreSQL is installed and running")
        print("2. The DATABASE_URL in .env is correct")
        print("3. The postgres user has the right permissions")
        return False
    
    return True

if __name__ == "__main__":
    print("Setting up database...")
    if create_database():
        print("\nNext steps:")
        print("1. Run 'python test_connection.py' to test connections")
        print("2. Run 'uvicorn app.main:app --reload' to start the application") 