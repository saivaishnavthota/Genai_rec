#!/usr/bin/env python3
"""
Database migration script to create interview scheduling tables
Run this script to add the new tables for interview scheduling system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.config import settings
from app.database import get_db

def create_interview_tables():
    """Create the new tables for interview scheduling"""
    
    # Create interview_schedules table
    interview_schedules_sql = """
    CREATE TABLE IF NOT EXISTS interview_schedules (
        id SERIAL PRIMARY KEY,
        application_id INTEGER REFERENCES applications(id) UNIQUE,
        
        -- Availability Management
        availability_requested_at TIMESTAMP,
        available_slots JSON,
        slots_generated_from DATE,
        slots_generated_to DATE,
        
        -- Candidate Selection
        selected_slot_date DATE,
        selected_slot_time TIME,
        candidate_selected_at TIMESTAMP,
        
        -- Interview Details
        primary_interviewer_email VARCHAR(255),
        primary_interviewer_name VARCHAR(255),
        backup_interviewer_email VARCHAR(255),
        backup_interviewer_name VARCHAR(255),
        interview_scheduled_at TIMESTAMP,
        interview_duration INTEGER DEFAULT 60,
        
        -- Status Tracking
        status VARCHAR(50) DEFAULT 'pending',
        notes TEXT,
        
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # Create interview_reviews table
    interview_reviews_sql = """
    CREATE TABLE IF NOT EXISTS interview_reviews (
        id SERIAL PRIMARY KEY,
        application_id INTEGER REFERENCES applications(id),
        interview_schedule_id INTEGER REFERENCES interview_schedules(id),
        
        -- Review Source
        interviewer_email VARCHAR(255),
        review_email_subject VARCHAR(500),
        review_email_body TEXT,
        review_received_at TIMESTAMP,
        
        -- Parsed Scores (1-10 scale)
        technical_score INTEGER,
        communication_score INTEGER,
        problem_solving_score INTEGER,
        cultural_fit_score INTEGER,
        leadership_potential INTEGER,
        
        -- Overall Assessment
        overall_recommendation VARCHAR(20),
        strengths TEXT,
        areas_for_improvement TEXT,
        additional_comments TEXT,
        
        -- Processing Status
        is_valid_format BOOLEAN DEFAULT FALSE,
        processed_at TIMESTAMP,
        processing_errors TEXT,
        
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # Extend applications table
    extend_applications_sql = """
    ALTER TABLE applications 
    ADD COLUMN IF NOT EXISTS interview_schedule_id INTEGER REFERENCES interview_schedules(id),
    ADD COLUMN IF NOT EXISTS interview_review_id INTEGER REFERENCES interview_reviews(id),
    ADD COLUMN IF NOT EXISTS selection_email_sent_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS hr_notification_sent_at TIMESTAMP,
    ADD COLUMN IF NOT EXISTS final_interview_score DECIMAL(5,2);
    """
    
    try:
        # Get database connection
        engine = create_engine(settings.database_url)
        
        with engine.connect() as connection:
            print("🗄️ Creating interview_schedules table...")
            connection.execute(text(interview_schedules_sql))
            connection.commit()
            
            print("🗄️ Creating interview_reviews table...")
            connection.execute(text(interview_reviews_sql))
            connection.commit()
            
            print("🗄️ Extending applications table...")
            connection.execute(text(extend_applications_sql))
            connection.commit()
            
            print("✅ All tables created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
        
    return True

if __name__ == "__main__":
    print("🚀 Starting database migration for interview scheduling...")
    success = create_interview_tables()
    if success:
        print("🎉 Database migration completed successfully!")
    else:
        print("💥 Database migration failed!")
        sys.exit(1)
