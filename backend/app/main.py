from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .database import create_tables
from .config import settings
from .api import auth, jobs, applications, companies, users, interviews, interviewer_auth
import os

# Create FastAPI app
app = FastAPI(
    title="GenAI Hiring System",
    description="AI-Powered Candidate Shortlisting System",
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS - Dynamic origins based on environment
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Add FRONTEND_URL from environment if set
if hasattr(settings, 'frontend_url') and settings.frontend_url:
    frontend_url = settings.frontend_url
    if frontend_url not in origins:
        origins.append(frontend_url)
    # Also add without trailing slash
    if frontend_url.endswith('/'):
        origins.append(frontend_url.rstrip('/'))

print(f"🌐 CORS allowed origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600  # Cache preflight requests for 1 hour
)

# Create upload directory
os.makedirs(settings.upload_dir, exist_ok=True)

# Mount static files for resume uploads
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(companies.router, prefix="/api/companies", tags=["Companies"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["Interviews"])
app.include_router(interviewer_auth.router, prefix="/api/interviewer", tags=["Interviewer Authentication"])

# Import and include resume update router
from .api import resume_update, scheduler
app.include_router(resume_update.router, prefix="/api", tags=["Resume Update"])
app.include_router(scheduler.router, prefix="/api", tags=["Scheduler"])

# Include AI Interview routers
from .ai_interview.routers import ai_interview_router
app.include_router(ai_interview_router, prefix="/api", tags=["AI Interview"])

# Health check endpoints
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/healthz")
async def healthz():
    """Kubernetes health check endpoint"""
    return {"status": "ok"}

@app.get("/readyz")
async def readyz():
    """Kubernetes readiness check endpoint"""
    # Check database connection
    try:
        from .database import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        return {"status": "ready"}
    except Exception as e:
        return {"status": "not_ready", "error": str(e)}, 503

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "GenAI Hiring System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

# Create database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    
    # Start the background scheduler for resume update emails
    import asyncio
    from .services.scheduler_service import run_background_scheduler
    asyncio.create_task(run_background_scheduler())
    print("✅ Background scheduler started for resume update emails")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug
    )
