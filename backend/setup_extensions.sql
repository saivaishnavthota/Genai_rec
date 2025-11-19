-- PostgreSQL Extensions Setup for AI Interview Module
-- Run this SQL script BEFORE running alembic upgrade head

-- Required: UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Optional: Full-text search with trigrams
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Optional: Vector similarity search (requires pgvector installation)
-- Install pgvector first: https://github.com/pgvector/pgvector
-- Then uncomment the line below:
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- Verify extensions
SELECT extname, extversion FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm', 'vector');

