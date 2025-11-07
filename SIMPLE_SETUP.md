
# Simple Setup Guide - AI Interview Demo

## Step 1: Install Backend Dependencies

Open a terminal in the `backend` folder and run:

```bash
pip install -r requirements.txt
```

This installs all Python packages including:
- FastAPI, SQLAlchemy, Alembic
- faster-whisper (for transcription)
- minio (for storage)
- opencv-python, numpy (for proctoring)

## Step 2: Setup Database Extensions

Run this once to create required PostgreSQL extensions:

```bash
cd backend
python setup-extensions.py
```

## Step 3: Run Database Migrations

```bash
cd backend
alembic upgrade head
```

## Step 4: Install Frontend Dependencies

Open a terminal in the `frontend` folder and run:

```bash
npm install
```

This installs React, TypeScript, MediaPipe, and other frontend packages.

## Step 5: Start the Backend

In the `backend` folder:

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Wait for: `Application startup complete`

## Step 6: Start the Frontend

Open a NEW terminal in the `frontend` folder:

```bash
npm start
```

Wait for: `webpack compiled successfully`

## Step 7: Access the Application

Open your browser:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## That's It!

Login to the system and navigate to an application to start an AI interview.

## Troubleshooting

**Backend won't start?**
- Check if PostgreSQL is running
- Check database connection in `.env` file
- Make sure port 8000 is not in use

**Frontend won't start?**
- Make sure port 3000 is not in use
- Try `npm install` again

**Database errors?**
- Run `python setup-extensions.py` again
- Run `alembic upgrade head` again

## Optional: MinIO (for file storage)

If you want to test file uploads, start MinIO:

```bash
docker run -p 9000:9000 -p 9001:9001 -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin minio/minio server /data --console-address :9001
```

Or skip it - the app will work without it for demo purposes.

