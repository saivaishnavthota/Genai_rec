-- GenAI Hiring System Database Initialization
-- This script runs automatically when PostgreSQL container starts for the first time

\echo 'Starting GenAI Hiring System database initialization...'

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Set timezone
SET timezone = 'UTC';

\echo 'Database extensions created successfully.'

-- Create indexes for better performance (these will be created after tables exist)
-- Note: Actual table creation is handled by SQLAlchemy migrations in the application

\echo 'GenAI Hiring System database initialization completed.'
