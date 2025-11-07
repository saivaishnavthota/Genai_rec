#!/usr/bin/env python3

import os
import sys
sys.path.append('/app')

from sqlalchemy import create_engine, text
from app.config import settings

def add_google_meet_columns():
    """Add Google Meet integration columns to interview_schedules table"""
    
    # Create database connection
    engine = create_engine(settings.database_url)
    
    try:
        with engine.connect() as conn:
            print("🔄 Adding Google Meet integration columns...")
            
            # Add Google Meet columns to interview_schedules table
            alter_statements = [
                "ALTER TABLE interview_schedules ADD COLUMN IF NOT EXISTS google_meet_link VARCHAR(500);",
                "ALTER TABLE interview_schedules ADD COLUMN IF NOT EXISTS google_calendar_event_id VARCHAR(255);",
                "ALTER TABLE interview_schedules ADD COLUMN IF NOT EXISTS google_meet_created TIMESTAMP;"
            ]
            
            for statement in alter_statements:
                conn.execute(text(statement))
                print(f"✅ Executed: {statement}")
            
            conn.commit()
            print("✅ Google Meet columns added successfully!")
            
    except Exception as e:
        print(f"❌ Error adding Google Meet columns: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== ADDING GOOGLE MEET INTEGRATION COLUMNS ===")
    success = add_google_meet_columns()
    if success:
        print("🎉 Database migration completed successfully!")
    else:
        print("💥 Database migration failed!")
        sys.exit(1)
