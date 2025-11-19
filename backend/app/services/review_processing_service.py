from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from ..models.application import Application
from ..models.interview_schedule import InterviewSchedule
from ..models.interview_review import InterviewReview
from ..config import settings
import logging
import re

logger = logging.getLogger(__name__)

class ReviewProcessingService:
    def __init__(self):
        pass
    
    def parse_review_email(self, email_subject: str, email_body: str) -> dict:
        """
        Parse structured review email and extract scores
        Expected format:
        CANDIDATE: [Name]
        POSITION: [Title]
        INTERVIEW DATE: [Date]
        INTERVIEWER: [Name]
        
        SCORING (Rate 1-10):
        Technical Skills: [Score]/10
        Communication: [Score]/10
        Problem Solving: [Score]/10
        Cultural Fit: [Score]/10
        Leadership Potential: [Score]/10
        
        OVERALL RECOMMENDATION: [Hire/Reject/Maybe]
        
        STRENGTHS:
        - [List]
        
        AREAS FOR IMPROVEMENT:
        - [List]
        
        ADDITIONAL COMMENTS:
        [Comments]
        """
        parsed_data = {
            "candidate_name": None,
            "position": None,
            "interview_date": None,
            "interviewer": None,
            "technical_score": None,
            "communication_score": None,
            "problem_solving_score": None,
            "cultural_fit_score": None,
            "leadership_potential": None,
            "overall_recommendation": None,
            "strengths": None,
            "areas_for_improvement": None,
            "additional_comments": None,
            "is_valid": False
        }
        
        try:
            # Extract candidate name
            candidate_match = re.search(r'CANDIDATE:\s*(.+)', email_body, re.IGNORECASE)
            if candidate_match:
                parsed_data["candidate_name"] = candidate_match.group(1).strip()
            
            # Extract position
            position_match = re.search(r'POSITION:\s*(.+)', email_body, re.IGNORECASE)
            if position_match:
                parsed_data["position"] = position_match.group(1).strip()
            
            # Extract interview date
            date_match = re.search(r'INTERVIEW DATE:\s*(.+)', email_body, re.IGNORECASE)
            if date_match:
                parsed_data["interview_date"] = date_match.group(1).strip()
            
            # Extract interviewer
            interviewer_match = re.search(r'INTERVIEWER:\s*(.+)', email_body, re.IGNORECASE)
            if interviewer_match:
                parsed_data["interviewer"] = interviewer_match.group(1).strip()
            
            # Extract scores (1-10 scale)
            score_patterns = {
                "technical_score": r'Technical Skills:\s*(\d+)/?10',
                "communication_score": r'Communication:\s*(\d+)/?10',
                "problem_solving_score": r'Problem Solving:\s*(\d+)/?10',
                "cultural_fit_score": r'Cultural Fit:\s*(\d+)/?10',
                "leadership_potential": r'Leadership Potential:\s*(\d+)/?10'
            }
            
            for score_key, pattern in score_patterns.items():
                match = re.search(pattern, email_body, re.IGNORECASE)
                if match:
                    score = int(match.group(1))
                    if 1 <= score <= 10:
                        parsed_data[score_key] = score
            
            # Extract overall recommendation
            recommendation_match = re.search(r'OVERALL RECOMMENDATION:\s*(\w+)', email_body, re.IGNORECASE)
            if recommendation_match:
                recommendation = recommendation_match.group(1).strip().lower()
                if recommendation in ['hire', 'reject', 'maybe']:
                    parsed_data["overall_recommendation"] = recommendation
            
            # Extract strengths
            strengths_match = re.search(r'STRENGTHS:\s*(.+?)(?=AREAS FOR IMPROVEMENT:|ADDITIONAL COMMENTS:|$)', email_body, re.IGNORECASE | re.DOTALL)
            if strengths_match:
                parsed_data["strengths"] = strengths_match.group(1).strip()
            
            # Extract areas for improvement
            areas_match = re.search(r'AREAS FOR IMPROVEMENT:\s*(.+?)(?=ADDITIONAL COMMENTS:|$)', email_body, re.IGNORECASE | re.DOTALL)
            if areas_match:
                parsed_data["areas_for_improvement"] = areas_match.group(1).strip()
            
            # Extract additional comments
            comments_match = re.search(r'ADDITIONAL COMMENTS:\s*(.+?)(?=INTERVIEWER SIGNATURE:|DATE:|$)', email_body, re.IGNORECASE | re.DOTALL)
            if comments_match:
                parsed_data["additional_comments"] = comments_match.group(1).strip()
            
            # Validate if review has minimum required fields
            parsed_data["is_valid"] = self.validate_review_format(parsed_data)
            
        except Exception as e:
            logger.error(f"Error parsing review email: {e}")
            parsed_data["parsing_error"] = str(e)
        
        return parsed_data
    
    def validate_review_format(self, parsed_data: dict) -> bool:
        """
        Validate if review follows the required format
        """
        required_fields = [
            "candidate_name",
            "technical_score",
            "communication_score", 
            "problem_solving_score",
            "cultural_fit_score",
            "overall_recommendation"
        ]
        
        for field in required_fields:
            if not parsed_data.get(field):
                return False
        
        # Validate scores are in range
        score_fields = [
            "technical_score",
            "communication_score",
            "problem_solving_score", 
            "cultural_fit_score",
            "leadership_potential"
        ]
        
        for field in score_fields:
            score = parsed_data.get(field)
            if score is not None and (score < 1 or score > 10):
                return False
        
        return True
    
    def calculate_overall_score(self, scores: dict) -> float:
        """
        Calculate weighted overall interview score
        """
        try:
            # Define weights for different criteria
            weights = {
                "technical_score": 0.35,      # 35% - Most important for technical roles
                "communication_score": 0.25,  # 25% - Important for collaboration
                "problem_solving_score": 0.25, # 25% - Critical thinking
                "cultural_fit_score": 0.10,   # 10% - Team fit
                "leadership_potential": 0.05   # 5% - Future potential
            }
            
            total_score = 0.0
            total_weight = 0.0
            
            for score_field, weight in weights.items():
                score = scores.get(score_field)
                if score is not None:
                    total_score += score * weight
                    total_weight += weight
            
            # Calculate weighted average
            if total_weight > 0:
                return round((total_score / total_weight) * 10, 2)  # Convert to percentage
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 0.0
    
    async def process_and_update_application(self, db: Session, application_id: int, review_data: dict) -> dict:
        """
        Process review data and update application
        """
        try:
            application = db.query(Application).filter(Application.id == application_id).first()
            if not application:
                raise ValueError(f"Application {application_id} not found")
            
            interview_schedule = db.query(InterviewSchedule).filter(
                InterviewSchedule.application_id == application_id
            ).first()
            
            # Create interview review record
            interview_review = InterviewReview(
                application_id=application_id,
                interview_schedule_id=interview_schedule.id if interview_schedule else None,
                interviewer_email=review_data.get("interviewer_email"),
                review_email_subject=review_data.get("email_subject"),
                review_email_body=review_data.get("email_body"),
                review_received_at=datetime.utcnow(),
                technical_score=review_data.get("technical_score"),
                communication_score=review_data.get("communication_score"),
                problem_solving_score=review_data.get("problem_solving_score"),
                cultural_fit_score=review_data.get("cultural_fit_score"),
                leadership_potential=review_data.get("leadership_potential"),
                overall_recommendation=review_data.get("overall_recommendation"),
                strengths=review_data.get("strengths"),
                areas_for_improvement=review_data.get("areas_for_improvement"),
                additional_comments=review_data.get("additional_comments"),
                is_valid_format=review_data.get("is_valid", False),
                processed_at=datetime.utcnow()
            )
            
            db.add(interview_review)
            db.flush()  # Get the ID
            
            # Calculate overall interview score
            overall_score = self.calculate_overall_score(review_data)
            
            # Update application with review data
            application.interview_review_id = interview_review.id
            application.final_interview_score = overall_score
            application.status = "review_received"
            
            db.commit()
            
            return {
                "success": True,
                "message": "Review processed successfully",
                "review_id": interview_review.id,
                "overall_score": overall_score,
                "recommendation": review_data.get("overall_recommendation"),
                "is_valid_format": review_data.get("is_valid", False)
            }
            
        except Exception as e:
            logger.error(f"Error processing review for application {application_id}: {e}")
            db.rollback()
            return {"success": False, "message": str(e)}
    
    async def process_review_email(self, db: Session, email_data: dict) -> dict:
        """
        Process incoming review email from interviewer
        """
        try:
            # Parse the email content
            parsed_review = self.parse_review_email(
                email_data.get("subject", ""),
                email_data.get("body", "")
            )
            
            if not parsed_review["is_valid"]:
                return {
                    "success": False,
                    "message": "Invalid review format",
                    "parsed_data": parsed_review
                }
            
            # Try to find the application by candidate name and interviewer email
            candidate_name = parsed_review["candidate_name"]
            interviewer_email = email_data.get("from_email")
            
            # Find application with matching candidate name and interviewer
            application = db.query(Application).join(
                InterviewSchedule, Application.id == InterviewSchedule.application_id
            ).filter(
                Application.full_name.ilike(f"%{candidate_name}%"),
                InterviewSchedule.primary_interviewer_email == interviewer_email
            ).first()
            
            if not application:
                # Try backup interviewer
                application = db.query(Application).join(
                    InterviewSchedule, Application.id == InterviewSchedule.application_id
                ).filter(
                    Application.full_name.ilike(f"%{candidate_name}%"),
                    InterviewSchedule.backup_interviewer_email == interviewer_email
                ).first()
            
            if not application:
                return {
                    "success": False,
                    "message": f"No matching application found for candidate: {candidate_name}",
                    "parsed_data": parsed_review
                }
            
            # Process the review
            review_data = {
                **parsed_review,
                "interviewer_email": interviewer_email,
                "email_subject": email_data.get("subject"),
                "email_body": email_data.get("body")
            }
            
            result = await self.process_and_update_application(db, application.id, review_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing review email: {e}")
            return {"success": False, "message": str(e)}
    
    def get_review_template(self, candidate_name: str, job_title: str) -> str:
        """
        Generate review template for interviewer
        """
        template = f"""
Subject: Interview Review - {candidate_name} - {job_title}

CANDIDATE: {candidate_name}
POSITION: {job_title}
INTERVIEW DATE: [Enter Date]
INTERVIEWER: [Your Name]

SCORING (Rate 1-10, where 10 is excellent):
Technical Skills: [Score]/10
Communication: [Score]/10
Problem Solving: [Score]/10
Cultural Fit: [Score]/10
Leadership Potential: [Score]/10

OVERALL RECOMMENDATION: [Hire/Reject/Maybe]

STRENGTHS:
- [List key strengths observed]
- 
- 

AREAS FOR IMPROVEMENT:
- [List areas that need development]
- 
- 

ADDITIONAL COMMENTS:
[Any other observations or notes]

INTERVIEWER SIGNATURE: [Your Name]
DATE: [Date]
        """.strip()
        
        return template
