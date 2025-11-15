-- GenAI Hiring System Database Initialization
-- This script runs automatically when PostgreSQL container starts for the first time

\echo 'Starting GenAI Hiring System database initialization...'

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Set timezone
SET timezone = 'UTC';

\echo 'Database extensions created successfully.'

-- Create indexes for better performance (these will be created after tables exist)
-- Note: Actual table creation is handled by SQLAlchemy migrations in the application

-- Add missing score_explanation column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'application_scores' 
        AND column_name = 'score_explanation'
    ) THEN
        ALTER TABLE application_scores ADD COLUMN score_explanation TEXT;
    END IF;
END $$;

\echo 'GenAI Hiring System database initialization completed.'
