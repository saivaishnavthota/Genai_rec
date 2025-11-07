from .proctor import router as proctor_router
from .asr import router as asr_router
from .scoring import router as scoring_router
from .kb import router as kb_router
from .review import router as review_router

# Combine all routers into a single router
from fastapi import APIRouter

ai_interview_router = APIRouter()
ai_interview_router.include_router(proctor_router, prefix="/ai-interview", tags=["AI Interview"])
ai_interview_router.include_router(asr_router, prefix="/ai-interview", tags=["AI Interview - ASR"])
ai_interview_router.include_router(scoring_router, prefix="/ai-interview", tags=["AI Interview - Scoring"])
ai_interview_router.include_router(kb_router, prefix="/ai-interview/kb", tags=["AI Interview - Knowledge Base"])
ai_interview_router.include_router(review_router, prefix="/ai-interview/review", tags=["AI Interview - Review"])

__all__ = [
    "proctor_router",
    "asr_router",
    "scoring_router",
    "kb_router",
    "review_router",
]

