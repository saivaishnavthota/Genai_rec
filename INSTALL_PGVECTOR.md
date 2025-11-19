# Installing pgvector Extension

The `vector` extension is required for vector similarity search in the knowledge base. If you see an error about the vector extension not being available, follow these steps:

## Windows Installation

### Option 1: Pre-compiled (Easiest)

1. Download pre-compiled DLL from: https://github.com/pgvector/pgvector/releases
2. Copy `vector.dll` to your PostgreSQL `lib` directory:
   ```
   C:\Program Files\PostgreSQL\17\lib\
   ```
3. Copy `vector.control` and `vector--*.sql` files to:
   ```
   C:\Program Files\PostgreSQL\17\share\extension\
   ```
4. Restart PostgreSQL service
5. Run in PostgreSQL:
   ```sql
   CREATE EXTENSION vector;
   ```

### Option 2: Build from Source

1. Install Visual Studio Build Tools
2. Install PostgreSQL development headers
3. Clone and build:
   ```bash
   git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
   cd pgvector
   make
   make install
   ```
4. Restart PostgreSQL
5. Run: `CREATE EXTENSION vector;`

## Linux Installation

```bash
# Ubuntu/Debian
sudo apt install postgresql-17-pgvector

# Or build from source
git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install
```

## macOS Installation

```bash
brew install pgvector
```

## Verify Installation

```sql
-- Check if extension is available
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Create extension
CREATE EXTENSION vector;

-- Verify
SELECT extversion FROM pg_extension WHERE extname = 'vector';
```

## Temporary Workaround

If you can't install pgvector immediately, the migration will continue without it. The `kb_docs.embedding` column will be stored as text, and you can migrate to vector later:

```sql
-- After installing pgvector
ALTER TABLE kb_docs ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector;
```

## Note

- Vector extension is optional for basic functionality
- RAG scoring will work without it (using BM25 only)
- Full vector search requires the extension

