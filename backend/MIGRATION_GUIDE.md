# Database Migration Guide

This project uses **Alembic** for database migrations. Migrations allow you to version control your database schema and apply changes incrementally.

## Initial Setup

If this is the first time setting up migrations, run:

```bash
cd backend
python -m alembic upgrade head
```

This will create the `alembic_version` table in your database to track migration history.

## Common Migration Commands

### Create a New Migration

When you modify a model in `app/models/`, create a migration:

```bash
# Auto-generate migration from model changes
python -m alembic revision --autogenerate -m "Description of changes"

# Or create an empty migration file
python -m alembic revision -m "Description of changes"
```

### Apply Migrations

```bash
# Apply all pending migrations
python -m alembic upgrade head

# Apply specific migration
python -m alembic upgrade <revision_id>

# Apply one migration at a time
python -m alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback one migration
python -m alembic downgrade -1

# Rollback to specific revision
python -m alembic downgrade <revision_id>

# Rollback all migrations
python -m alembic downgrade base
```

### Check Migration Status

```bash
# Show current revision
python -m alembic current

# Show migration history
python -m alembic history

# Show pending migrations
python -m alembic heads
```

## Workflow

1. **Modify Models**: Edit models in `app/models/`
2. **Create Migration**: Run `alembic revision --autogenerate -m "description"`
3. **Review Migration**: Check the generated file in `alembic/versions/`
4. **Edit if Needed**: Manually adjust the migration if auto-generation missed something
5. **Apply Migration**: Run `alembic upgrade head`
6. **Test**: Verify the changes work correctly

## Important Notes

- **Always review auto-generated migrations** - Alembic might miss some changes
- **Test migrations on a copy** of your database before applying to production
- **Never edit existing migrations** that have been applied to production
- **Create new migrations** for any schema changes

## Example: Adding a New Column

```python
# 1. Modify the model in app/models/user.py
class User(Base):
    # ... existing fields ...
    new_field = Column(String, nullable=True)

# 2. Generate migration
python -m alembic revision --autogenerate -m "Add new_field to users"

# 3. Review the generated file in alembic/versions/

# 4. Apply migration
python -m alembic upgrade head
```

## Troubleshooting

### Migration Conflicts

If you have multiple migration branches:
```bash
# Merge branches
python -m alembic merge -m "Merge branches" <revision1> <revision2>
```

### Reset Database (Development Only)

⚠️ **WARNING**: This will delete all data!

```bash
# Drop all tables
python -m alembic downgrade base

# Recreate from migrations
python -m alembic upgrade head
```

### Check SQL Without Applying

```bash
# Show SQL for upgrade
python -m alembic upgrade head --sql

# Show SQL for downgrade
python -m alembic downgrade -1 --sql
```

## Migration Files Location

All migration files are stored in:
```
backend/alembic/versions/
```

Each file follows the naming pattern:
```
<revision_id>_<description>.py
```

## Integration with Application

The application will automatically create tables on startup using `create_tables()` for development. In production, use migrations instead:

```python
# In production, run migrations instead of create_tables()
# Remove or comment out this line in app/main.py:
# create_tables()  # Only for development
```

Then run migrations manually:
```bash
python -m alembic upgrade head
```

