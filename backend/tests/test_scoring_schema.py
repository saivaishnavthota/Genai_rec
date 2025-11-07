"""Tests for scoring schema validation"""
import pytest
from decimal import Decimal
from app.ai_interview.schemas.scoring import ScoreOut, CriteriaScore, Citation


def test_score_out_schema():
    """Test ScoreOut schema validation"""
    criteria = [
        CriteriaScore(
            criterion_name="Technical Knowledge",
            score=Decimal("8.5"),
            explanation="Strong technical understanding",
            citations=[]
        )
    ]
    
    score = ScoreOut(
        criteria=criteria,
        final_score=Decimal("8.2"),
        citations=[],
        summary="Overall good performance",
        improvement_tip="Could improve in communication"
    )
    
    assert score.final_score == Decimal("8.2")
    assert len(score.criteria) == 1
    assert score.summary is not None


def test_score_out_with_citations():
    """Test ScoreOut with citations"""
    citation = Citation(
        doc_id=1,
        section="Technical",
        relevance_score=0.9,
        excerpt="Relevant excerpt"
    )
    
    criteria = [
        CriteriaScore(
            criterion_name="Technical Knowledge",
            score=Decimal("8.5"),
            explanation="Strong technical understanding",
            citations=[citation]
        )
    ]
    
    score = ScoreOut(
        criteria=criteria,
        final_score=Decimal("8.2"),
        citations=[citation],
        summary="Overall good performance"
    )
    
    assert len(score.citations) > 0
    assert len(score.criteria[0].citations) > 0


def test_score_out_validation():
    """Test ScoreOut validation (score must be 0-10)"""
    with pytest.raises(Exception):  # Should raise validation error
        ScoreOut(
            criteria=[],
            final_score=Decimal("11.0"),  # Invalid: > 10
            citations=[],
            summary="Test"
        )


def test_criteria_score_validation():
    """Test CriteriaScore validation"""
    with pytest.raises(Exception):
        CriteriaScore(
            criterion_name="Test",
            score=Decimal("-1.0"),  # Invalid: < 0
            explanation="Test",
            citations=[]
        )

