"""Scoring schemas"""
from typing import Optional, List
from decimal import Decimal
from pydantic import Field
from .base import BaseSchema


class Citation(BaseSchema):
    """Citation reference to KB document"""
    doc_id: int = Field(..., description="Knowledge base document ID")
    section: Optional[str] = Field(None, description="Section within document")
    relevance_score: float = Field(..., ge=0.0, le=1.0, description="Relevance score")
    excerpt: Optional[str] = Field(None, description="Relevant excerpt from document")


class CriteriaScore(BaseSchema):
    """Score for a single rubric criterion"""
    criterion_name: str = Field(..., description="Name of the criterion")
    score: Decimal = Field(..., ge=0, le=10, description="Score out of 10")
    explanation: str = Field(..., description="Explanation for the score")
    citations: List[Citation] = Field(default_factory=list, description="Supporting citations")


class ScoreOut(BaseSchema):
    """Final scoring output"""
    criteria: List[CriteriaScore] = Field(..., description="Scores for each criterion")
    final_score: Decimal = Field(..., ge=0, le=10, description="Final score out of 10")
    citations: List[Citation] = Field(default_factory=list, description="All citations")
    summary: str = Field(..., description="Overall summary")
    improvement_tip: Optional[str] = Field(None, description="Tip for improvement")


class ScoringRequest(BaseSchema):
    """Request for scoring an interview session"""
    session_id: int = Field(..., description="Session ID to score")


class ReviewDecisionRequest(BaseSchema):
    """Request for HR review decision"""
    status: str = Field(..., pattern="^(PASS|REVIEW|FAIL)$", description="Final decision")
    notes: Optional[str] = Field(None, description="Review notes")

