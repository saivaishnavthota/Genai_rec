# Fix Database Connection Error

## Problem
You're getting this error:
```
psycopg2.OperationalError: password authentication failed for user "postgres"
```

This means the PostgreSQL password in your configuration doesn't match your actual PostgreSQL password.

## Solution Options

### Option 1: Create/Update .env File (Recommended)

1. **Create a `.env` file in the `backend` directory** (or root directory):

```bash
cd backend
copy ..\env.example .env
```

2. **Edit the `.env` file** and update these lines with your actual PostgreSQL credentials:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_postgres_password
POSTGRES_DB=genai_hiring
DATABASE_URL=postgresql://postgres:your_actual_postgres_password@localhost:5432/genai_hiring
```

3. **Replace `your_actual_postgres_password`** with your real PostgreSQL password

### Option 2: Change PostgreSQL Password

If you want to use the default password "vaishnav":

**Windows (using psql):**
```bash
# Connect to PostgreSQL
psql -U postgres

# Change password
ALTER USER postgres PASSWORD 'vaishnav';
\q
```

**Or using SQL command:**
```bash
psql -U postgres -c "ALTER USER postgres PASSWORD 'vaishnav';"
```

### Option 3: Use Docker for PostgreSQL (Easiest)

If you don't want to manage PostgreSQL manually:

1. **Start only PostgreSQL and Redis in Docker:**
```bash
docker-compose up postgres redis
```

2. **Use the default Docker password** in your `.env`:
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=genai_hiring
DATABASE_URL=postgresql://postgres:password@localhost:5432/genai_hiring
```

3. **Then run backend manually:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Quick Fix Steps

1. **Find your PostgreSQL password** (if you forgot it, see "Reset PostgreSQL Password" below)

2. **Create `.env` file in backend directory:**
```bash
cd backend
```

Create a file named `.env` with:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD_HERE@localhost:5432/genai_hiring
POSTGRES_USER=postgres
POSTGRES_PASSWORD=YOUR_PASSWORD_HERE
POSTGRES_DB=genai_hiring
```

3. **Replace `YOUR_PASSWORD_HERE`** with your actual password

4. **Restart the backend server**

## Reset PostgreSQL Password (If You Forgot)

### Windows

1. **Stop PostgreSQL service:**
```bash
net stop postgresql-x64-15
```
(Replace `postgresql-x64-15` with your PostgreSQL service name)

2. **Edit `pg_hba.conf`** (usually in `C:\Program Files\PostgreSQL\15\data\pg_hba.conf`)

3. **Change this line:**
```
host    all             all             127.0.0.1/32            md5
```
**To:**
```
host    all             all             127.0.0.1/32            trust
```

4. **Start PostgreSQL:**
```bash
net start postgresql-x64-15
```

5. **Connect and change password:**
```bash
psql -U postgres
ALTER USER postgres PASSWORD 'vaishnav';
```

6. **Revert `pg_hba.conf` back to `md5`** and restart PostgreSQL

### Alternative: Use pgAdmin
- Open pgAdmin
- Right-click on server → Properties → Change password

## Verify Connection

Test your connection:
```bash
psql -U postgres -d genai_hiring
```

Or test from Python:
```python
import psycopg2
conn = psycopg2.connect(
    host="localhost",
    database="genai_hiring",
    user="postgres",
    password="your_password"
)
print("Connected successfully!")
conn.close()
```

## After Fixing

1. **Create the database** (if it doesn't exist):
```bash
psql -U postgres -c "CREATE DATABASE genai_hiring;"
```

2. **Initialize database tables:**
```bash
cd backend
python init_db.py
```

3. **Start the backend:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

You should now see the backend start without database errors!

