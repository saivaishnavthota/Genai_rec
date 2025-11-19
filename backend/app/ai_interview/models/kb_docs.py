"""
Knowledge Base Document Models (for RAG)
"""
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, JSON,
    Enum as SQLEnum, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import enum
import uuid
from ...database import Base

# Note: pgvector extension must be enabled in PostgreSQL
# For now, we'll use Text for embedding, migration will add vector type
try:
    from pgvector.sqlalchemy import Vector
    HAS_VECTOR = True
except ImportError:
    HAS_VECTOR = False
    # Fallback: use Text column, migration will handle vector conversion
    Vector = Text


class KBBucket(str, enum.Enum):
    """Knowledge base bucket types"""
    RUBRIC = "rubric"
    EXEMPLAR = "exemplar"
    POLICY = "policy"
    QBANK = "qbank"


class KBDocument(Base):
    """Knowledge base document for RAG"""
    __tablename__ = "kb_docs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    role = Column(String(100), nullable=True, index=True)  # e.g., "software_engineer"
    level = Column(String(50), nullable=True, index=True)  # e.g., "senior", "mid"
    topic = Column(String(200), nullable=True, index=True)  # e.g., "system_design"
    
    bucket = Column(
        SQLEnum(KBBucket, native_enum=False),
        nullable=False,
        index=True
    )
    
    version = Column(String(50), nullable=False, default="1.0")
    region = Column(String(50), nullable=True)  # e.g., "us", "eu", "asia"
    
    text = Column(Text, nullable=False)
    
    # Embedding vector (pgvector)
    # Migration will create proper vector type after extension is enabled
    embedding = Column(Text, nullable=True) if not HAS_VECTOR else Column(Vector(1536), nullable=True)
    
    meta = Column(JSON, nullable=True)  # Additional metadata
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_kb_role_level", "role", "level"),
        Index("idx_kb_bucket", "bucket"),
        Index("idx_kb_topic", "topic"),
        # Full-text search index (if pg_trgm enabled)
        # Index("idx_kb_text_gin", postgresql_using="gin", postgresql_ops={"text": "gin_trgm_ops"}),
    )

