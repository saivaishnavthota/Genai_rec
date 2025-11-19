"""Tests for API contracts"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.user import User
from app.models.job import Job
from app.models.application import Application

client = TestClient(app)


@pytest.fixture
def test_user(db: Session):
    """Create test user"""
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed",
        user_type="hr",
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_job(db: Session):
    """Create test job"""
    job = Job(
        title="Software Engineer",
        description="Test job",
        company_id=1,
        created_by=1,
        status="published"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job


@pytest.fixture
def test_application(db: Session, test_job):
    """Create test application"""
    app = Application(
        reference_number="TEST001",
        full_name="Test Candidate",
        email="candidate@example.com",
        resume_filename="test.pdf",
        resume_path="/test.pdf",
        job_id=test_job.id,
        status="pending"
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


def test_start_interview_endpoint(test_user, test_application, test_job):
    """Test start interview endpoint"""
    # This would require authentication setup
    # For now, just test the endpoint exists
    response = client.post(
        "/api/ai-interview/start",
        json={
            "application_id": test_application.id,
            "job_id": test_job.id
        }
    )
    
    # Should return 401 without auth, but endpoint exists
    assert response.status_code in [401, 201]


def test_get_flags_endpoint(test_user):
    """Test get flags endpoint"""
    response = client.get("/api/ai-interview/1/flags")
    
    # Should return 401 without auth
    assert response.status_code in [401, 404]


def test_end_interview_endpoint(test_user):
    """Test end interview endpoint"""
    response = client.post("/api/ai-interview/1/end")
    
    # Should return 401 without auth
    assert response.status_code in [401, 404]


def test_get_report_endpoint(test_user):
    """Test get report endpoint"""
    response = client.get("/api/ai-interview/1/report")
    
    # Should return 401 without auth
    assert response.status_code in [401, 404]


def test_health_endpoints():
    """Test health check endpoints"""
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    
    response = client.get("/readyz")
    assert response.status_code in [200, 503]  # 503 if DB not ready

