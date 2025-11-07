# Fixed: Alembic Migration Error

## Issue Resolved

The error `Attribute name 'metadata' is reserved when using the Declarative API` has been fixed.

## What Was Fixed

1. **Renamed `metadata` column** in `AISessionFlag` model to `flag_metadata` (SQLAlchemy reserved name)
2. **Updated migration** to use `flag_metadata` instead of `metadata`
3. **Updated schemas** to handle the alias mapping (API still returns `metadata` for compatibility)
4. **Made extensions optional** in migration to avoid transaction issues

## Current Status

✅ Migration runs successfully
✅ Tables are created
✅ Extensions are handled separately (manual setup)

## Next Steps

### 1. Create Extensions Manually (if not done)

Run this SQL in your PostgreSQL database:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

For vector extension (optional):
```sql
CREATE EXTENSION IF NOT EXISTS "vector";
```

### 2. Verify Migration

```bash
cd backend
alembic current
alembic upgrade head
```

### 3. Verify Tables Created

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('ai_interview_sessions', 'ai_proctor_flags', 'kb_docs');

-- Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename LIKE 'ai_%' OR tablename = 'kb_docs';
```

## What Changed

- **Model**: `metadata` → `flag_metadata` (database column)
- **Schema**: Uses alias so API still returns `metadata` (backward compatible)
- **Migration**: Extensions created manually, not in migration

## Testing

After migration, test the API:

```bash
# Start backend
cd backend
python -m uvicorn app.main:app --reload

# Check health
curl http://localhost:8000/healthz

# Check API docs
# Open http://localhost:8000/docs
```

The AI interview endpoints should now be available at:
- `POST /api/ai-interview/start`
- `GET /api/ai-interview/{session_id}/flags`
- etc.

