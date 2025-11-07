"""Knowledge base schemas"""
from typing import Optional, List
from datetime import datetime
from pydantic import Field
from .base import BaseSchema
from ..models.kb_docs import KBBucket


class KBDocumentOut(BaseSchema):
    """Knowledge base document output"""
    id: int
    role: Optional[str] = None
    level: Optional[str] = None
    topic: Optional[str] = None
    bucket: KBBucket
    version: str
    region: Optional[str] = None
    text: str
    meta: Optional[dict] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class KBIngestRequest(BaseSchema):
    """Request to ingest documents into knowledge base"""
    role: Optional[str] = Field(None, description="Role (e.g., software_engineer)")
    level: Optional[str] = Field(None, description="Level (e.g., senior, mid)")
    topic: Optional[str] = Field(None, description="Topic (e.g., system_design)")
    bucket: KBBucket = Field(..., description="Document bucket type")
    version: str = Field(default="1.0", description="Version")
    region: Optional[str] = Field(None, description="Region")
    text: str = Field(..., min_length=1, description="Document text")
    meta: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class KBSearchRequest(BaseSchema):
    """Knowledge base search request"""
    query: str = Field(..., min_length=1, description="Search query")
    role: Optional[str] = Field(None, description="Filter by role")
    level: Optional[str] = Field(None, description="Filter by level")
    topic: Optional[str] = Field(None, description="Filter by topic")
    bucket: Optional[KBBucket] = Field(None, description="Filter by bucket")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")


class KBSearchResponse(BaseSchema):
    """Knowledge base search response"""
    documents: List[KBDocumentOut] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results")
    query: str = Field(..., description="Original query")

