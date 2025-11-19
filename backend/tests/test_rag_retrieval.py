"""Tests for RAG retrieval"""
import pytest
from sqlalchemy.orm import Session
from app.ai_interview.models.kb_docs import KBDocument, KBBucket
from app.ai_interview.services.rag_service import RAGService


@pytest.fixture
def sample_kb_docs(db: Session):
    """Create sample KB documents for testing"""
    docs = [
        KBDocument(
            role="software_engineer",
            level="senior",
            topic="system_design",
            bucket=KBBucket.RUBRIC,
            version="1.0",
            text="Senior software engineers should demonstrate deep understanding of distributed systems, scalability patterns, and system architecture."
        ),
        KBDocument(
            role="software_engineer",
            level="mid",
            topic="coding",
            bucket=KBBucket.RUBRIC,
            version="1.0",
            text="Mid-level engineers should show proficiency in coding, problem-solving, and code review practices."
        ),
        KBDocument(
            role="data_scientist",
            level="senior",
            topic="machine_learning",
            bucket=KBBucket.RUBRIC,
            version="1.0",
            text="Senior data scientists should demonstrate expertise in ML algorithms, model evaluation, and production deployment."
        ),
    ]
    
    for doc in docs:
        db.add(doc)
    db.commit()
    
    return docs


def test_rag_search_by_role(db: Session, sample_kb_docs):
    """Test RAG search filters by role"""
    service = RAGService()
    
    results = service.search_kb(
        db,
        "software engineering",
        role="software_engineer",
        top_k=10
    )
    
    assert len(results) > 0
    assert all(doc.role == "software_engineer" for doc in results)


def test_rag_search_by_level(db: Session, sample_kb_docs):
    """Test RAG search filters by level"""
    service = RAGService()
    
    results = service.search_kb(
        db,
        "senior",
        level="senior",
        top_k=10
    )
    
    assert len(results) > 0
    assert all(doc.level == "senior" for doc in results)


def test_rag_search_by_bucket(db: Session, sample_kb_docs):
    """Test RAG search filters by bucket"""
    service = RAGService()
    
    results = service.search_kb(
        db,
        "rubric",
        bucket=KBBucket.RUBRIC,
        top_k=10
    )
    
    assert len(results) > 0
    assert all(doc.bucket == KBBucket.RUBRIC for doc in results)


def test_rag_search_returns_relevant_docs(db: Session, sample_kb_docs):
    """Test RAG search returns relevant documents"""
    service = RAGService()
    
    results = service.search_kb(
        db,
        "system design distributed systems",
        role="software_engineer",
        level="senior",
        top_k=5
    )
    
    assert len(results) > 0
    # Should find the system_design document
    assert any("distributed systems" in doc.text.lower() for doc in results)

