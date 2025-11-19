#!/usr/bin/env python3
"""
Database migration script to update interview_reviews table with missing columns
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings

def update_interview_reviews_table():
    """Add missing columns to interview_reviews table"""
    
    # Create database engine
    engine = create_engine(settings.database_url)
    
    # SQL commands to add missing columns
    alter_commands = [
        """
        ALTER TABLE interview_reviews 
        ADD COLUMN IF NOT EXISTS interviewer_name VARCHAR(255);
        """,
        """
        ALTER TABLE interview_reviews 
        ADD COLUMN IF NOT EXISTS interviewer_type VARCHAR(50);
        """,
        """
        ALTER TABLE interview_reviews 
        ADD COLUMN IF NOT EXISTS review_submitted_at TIMESTAMPTZ;
        """,
        """
        ALTER TABLE interview_reviews 
        ADD COLUMN IF NOT EXISTS overall_rating INTEGER;
        """
    ]
    
    try:
        with engine.connect() as connection:
            print("🔧 Updating interview_reviews table...")
            
            for i, command in enumerate(alter_commands, 1):
                try:
                    connection.execute(text(command))
                    print(f"✅ Step {i}: Added column successfully")
                except OperationalError as e:
                    if "already exists" in str(e):
                        print(f"ℹ️  Step {i}: Column already exists, skipping")
                    else:
                        print(f"❌ Step {i}: Error - {e}")
                        raise
            
            # Commit the changes
            connection.commit()
            print("✅ All columns added successfully!")
            
            # Verify the table structure
            result = connection.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'interview_reviews' 
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Updated table structure:")
            print("Column Name                | Data Type                | Nullable")
            print("-" * 70)
            for row in result:
                print(f"{row[0]:<25} | {row[1]:<23} | {row[2]}")
                
    except Exception as e:
        print(f"❌ Error updating table: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 Interview Reviews Table Migration")
    print("=" * 50)
    
    if update_interview_reviews_table():
        print("\n🎉 Migration completed successfully!")
        print("\n📝 Next steps:")
        print("1. Restart the backend container: docker-compose restart backend")
        print("2. Test the interviewer review submission")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
