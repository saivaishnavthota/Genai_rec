"""Knowledge base router"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
import logging
from typing import Optional
from ...database import get_db
from ...api.auth import get_current_user
from ...models.user import User
from ..schemas.kb import KBIngestRequest, KBSearchResponse, KBDocumentOut
from ..services.rag_service import RAGService
from ..models.kb_docs import KBBucket, KBDocument

logger = logging.getLogger(__name__)

router = APIRouter()

_rag_service = RAGService()


@router.post("/ingest", response_model=KBDocumentOut, status_code=status.HTTP_201_CREATED)
async def ingest_document(
    request: KBIngestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingest a document into the knowledge base
    
    Auth: Admin only
    """
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can ingest documents"
        )
    
    try:
        # Create document
        doc = KBDocument(
            role=request.role,
            level=request.level,
            topic=request.topic,
            bucket=request.bucket,
            version=request.version,
            region=request.region,
            text=request.text,
            meta=request.meta
        )
        
        db.add(doc)
        db.commit()
        db.refresh(doc)
        
        # TODO: Generate embedding and update doc.embedding
        
        return KBDocumentOut.model_validate(doc)
    except Exception as e:
        logger.error(f"Failed to ingest document: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/search", response_model=KBSearchResponse)
async def search_kb(
    q: str = Query(..., min_length=1, description="Search query"),
    role: Optional[str] = Query(None, description="Filter by role"),
    level: Optional[str] = Query(None, description="Filter by level"),
    topic: Optional[str] = Query(None, description="Filter by topic"),
    bucket: Optional[KBBucket] = Query(None, description="Filter by bucket"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search the knowledge base
    
    Auth: HR/Admin only
    """
    if current_user.user_type not in ["hr", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only HR and Admin can search KB"
        )
    
    try:
        docs = await _rag_service.search_kb(
            db,
            q,
            role=role,
            level=level,
            topic=topic,
            bucket=bucket,
            top_k=top_k
        )
        
        return KBSearchResponse(
            documents=[KBDocumentOut.model_validate(d) for d in docs],
            total=len(docs),
            query=q
        )
    except Exception as e:
        logger.error(f"Failed to search KB: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

