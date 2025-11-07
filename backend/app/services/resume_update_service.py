import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.application import Application, ApplicationScore
from ..models.job import Job
from ..models.resume_update_tracking import ResumeUpdateRequest, ResumeUpdateHistory, LLMEvaluationLog
from ..services.llm_service import LLMService
from ..services.scoring_service import ScoringService
from ..config import settings
from ..utils.resume_parser import parse_resume
from ..utils.email import send_email

logger = logging.getLogger(__name__)

class ResumeUpdateService:
    def __init__(self):
        self.llm_service = LLMService()
        self.scoring_service = ScoringService()
        self.shortlist_threshold = settings.shortlist_threshold  # 70
        self.max_update_attempts = 3
        self.email_interval_hours = 24

    async def evaluate_candidate_with_llm(
        self, 
        db: Session, 
        application: Application, 
        current_score: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Use LLM to evaluate if a candidate with score < 70 has potential
        Returns: (should_give_chance, reasoning, evaluation_details)
        """
        try:
            # Get job details
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if not job:
                raise ValueError(f"Job not found for application {application.id}")

            # Helper function to ensure we have a list
            def ensure_list(data):
                if isinstance(data, str):
                    import json
                    try:
                        return json.loads(data)
                    except:
                        return []
                return data if data is not None else []
            
            # Prepare candidate data
            candidate_data = {
                "name": application.full_name,
                "email": application.email,
                "skills": ensure_list(application.parsed_skills),
                "experience": ensure_list(application.parsed_experience),
                "education": ensure_list(application.parsed_education),
                "certifications": ensure_list(application.parsed_certifications),
                "current_score": current_score,
                "cover_letter": application.cover_letter,
                "additional_info": application.additional_info
            }

            # Prepare job requirements
            job_requirements = {
                "title": job.title or "Position",
                "description": job.description or "Job description not available",
                "key_skills": ensure_list(job.key_skills),
                "required_experience": job.required_experience or "Not specified",
                "certifications": ensure_list(job.certifications),
                "additional_requirements": ensure_list(job.additional_requirements),
                "experience_level": job.experience_level or "Not specified",
                "department": job.department or "Not specified"
            }

            # Create LLM prompt for evaluation
            prompt = self._create_llm_evaluation_prompt(candidate_data, job_requirements)
            
            # Log the evaluation attempt
            evaluation_log = LLMEvaluationLog(
                application_id=application.id,
                candidate_data=candidate_data,
                job_requirements=job_requirements,
                initial_score=current_score,
                llm_prompt=prompt,
                llm_response_raw="",  # Will be updated after LLM call
                llm_model_used=self.llm_service.ollama_model
            )
            
            start_time = datetime.now()
            
            # Call LLM for evaluation
            if self.llm_service.fallback_mode:
                logger.warning("LLM in fallback mode, using rule-based evaluation")
                result = self._fallback_evaluation(candidate_data, job_requirements, current_score, scoring_context)
                llm_response_raw = "FALLBACK_MODE: Rule-based evaluation used"
            else:
                try:
                    messages = [
                        {"role": "system", "content": "You are an expert HR professional evaluating candidates. Respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ]
                    
                    llm_response_raw = await self.llm_service._chat_ollama(messages, temperature=0.3, max_tokens=300)
                    result = self._parse_llm_evaluation_response(llm_response_raw)
                except Exception as llm_error:
                    logger.warning(f"LLM call failed: {llm_error}, falling back to rule-based evaluation")
                    result = self._fallback_evaluation(candidate_data, job_requirements, current_score, scoring_context)
                    llm_response_raw = f"LLM_ERROR: {str(llm_error)} - Used fallback evaluation"
            
            processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Update evaluation log
            evaluation_log.llm_response_raw = llm_response_raw
            evaluation_log.llm_response_parsed = result
            evaluation_log.evaluation_result = result.get("should_give_chance", False)
            evaluation_log.evaluation_confidence = result.get("confidence", 0.5)
            evaluation_log.evaluation_reasoning = result.get("reasoning", "")
            evaluation_log.processing_time_ms = processing_time
            
            db.add(evaluation_log)
            db.commit()
            
            logger.info(f"LLM evaluation completed for application {application.id}: {result}")
            
            return (
                result.get("should_give_chance", False),
                result.get("reasoning", "No specific reasoning provided"),
                result
            )
            
        except Exception as e:
            logger.error(f"Error in LLM evaluation for application {application.id}: {e}")
            # Fallback to conservative approach
            return False, f"Evaluation failed: {str(e)}", {"error": str(e)}

    def _create_llm_evaluation_prompt(self, candidate_data: Dict, job_requirements: Dict) -> str:
        """Create a detailed prompt for LLM evaluation"""
        
        # Safely convert lists to text, handling both strings and dicts
        def safe_join(items, separator=", "):
            if not items:
                return "None listed"
            text_items = []
            for item in items:
                if isinstance(item, dict):
                    # For experience: use title and company
                    if 'title' in item:
                        text_items.append(f"{item.get('title', '')} at {item.get('company', 'Unknown Company')}")
                    # For education: use degree and institution
                    elif 'degree' in item:
                        text_items.append(f"{item.get('degree', '')} from {item.get('institution', 'Unknown Institution')}")
                    else:
                        # Generic dict handling
                        text_items.append(str(item))
                else:
                    text_items.append(str(item))
            return separator.join(text_items)
        
        skills_text = safe_join(candidate_data["skills"])
        experience_text = safe_join(candidate_data["experience"], "; ")
        education_text = safe_join(candidate_data["education"], "; ")
        
        job_skills_text = ", ".join(job_requirements["key_skills"]) if job_requirements["key_skills"] else "None specified"
        
        prompt = f"""Evaluate this candidate for potential despite their low ATS score of {candidate_data['current_score']:.1f}/100.

**Job Requirements:**
- Position: {job_requirements['title']}
- Department: {job_requirements.get('department', 'Not specified')}
- Experience Level: {job_requirements.get('experience_level', 'Not specified')}
- Required Skills: {job_skills_text}
- Required Experience: {job_requirements.get('required_experience', 'Not specified')}
- Additional Requirements: {'; '.join(job_requirements.get('additional_requirements', []))}

**Candidate Profile:**
- Name: {candidate_data['name']}
- Current Score: {candidate_data['current_score']:.1f}/100 (below 70 threshold)
- Skills: {skills_text}
- Experience: {experience_text}
- Education: {education_text}
- Cover Letter: {(candidate_data.get('cover_letter') or 'Not provided')[:200]}...

**Evaluation Criteria:**
Look for hidden potential, transferable skills, growth mindset, relevant experience even if not perfectly matched, educational background that could compensate for experience gaps, and passion/motivation indicators.

**Instructions:**
Despite the low ATS score, evaluate if this candidate shows potential for the role. Consider:
1. Transferable skills that might not have been caught by ATS
2. Educational background that could compensate for experience
3. Growth potential and learning ability indicators
4. Passion and motivation shown in cover letter
5. Unique experiences that could bring value

Respond with ONLY valid JSON:
{{
  "should_give_chance": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Detailed explanation of your decision (2-3 sentences)",
  "key_strengths": ["list", "of", "identified", "strengths"],
  "improvement_areas": ["areas", "where", "resume", "could", "be", "improved"],
  "recommendation": "specific advice for candidate if given a chance"
}}

Be thorough but fair. Only recommend giving a chance if you genuinely see potential."""

        return prompt

    def _parse_llm_evaluation_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response and extract evaluation decision"""
        try:
            # Find JSON in response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response[json_start:json_end]
                result = json.loads(json_text)
                
                # Validate required fields
                if "should_give_chance" not in result:
                    result["should_give_chance"] = False
                
                if "reasoning" not in result:
                    result["reasoning"] = "No reasoning provided"
                
                if "confidence" not in result:
                    result["confidence"] = 0.5
                
                return result
            else:
                logger.warning("No valid JSON found in LLM response")
                return {
                    "should_give_chance": False,
                    "reasoning": "Failed to parse LLM response",
                    "confidence": 0.0
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            return {
                "should_give_chance": False,
                "reasoning": f"JSON parsing error: {str(e)}",
                "confidence": 0.0
            }

    def _fallback_evaluation(self, candidate_data: Dict, job_requirements: Dict, current_score: float, scoring_context: Dict[str, float] = None) -> Dict[str, Any]:
        """Fallback evaluation when LLM is not available"""
        
        # Enhanced rule-based evaluation using scoring context
        give_chance = False
        reasoning_parts = []
        confidence = 0.5
        
        # Use scoring context if available for more accurate evaluation
        if scoring_context:
            skills_match = scoring_context.get('skills_match', 0)
            experience_match = scoring_context.get('experience_match', 0)
            education_match = scoring_context.get('education_match', 0)
            ats_score = scoring_context.get('ats_score', 0)
            match_score = scoring_context.get('match_score', 0)
            
            # Rule 1: Strong skills or experience match (≥60%) with overall score ≥60%
            if (skills_match >= 60 or experience_match >= 60) and current_score >= 60:
                give_chance = True
                reasoning_parts.append(f"Strong potential: Skills match {skills_match:.1f}%, Experience match {experience_match:.1f}%")
                confidence += 0.3
            
            # Rule 2: Good overall match but low ATS (ATS dragging down the score)
            if match_score >= 70 and ats_score < 50:
                give_chance = True
                reasoning_parts.append(f"Good job fit ({match_score:.1f}% match) but poor ATS formatting ({ats_score:.1f}%)")
                confidence += 0.4
            
            # Rule 3: Score in improvement range (60-70)
            if 60 <= current_score < 70:
                give_chance = True
                reasoning_parts.append(f"Score {current_score:.1f}% is in improvement range")
                confidence += 0.2
            
            # Rule 4: Any component score ≥80% indicates strong potential
            if any(score >= 80 for score in [skills_match, experience_match, education_match]):
                give_chance = True
                high_scores = [name for name, score in [
                    ('skills', skills_match), ('experience', experience_match), ('education', education_match)
                ] if score >= 80]
                reasoning_parts.append(f"Excellent {', '.join(high_scores)} alignment")
                confidence += 0.3
        
        else:
            # Fallback to basic evaluation when no scoring context
            if current_score >= 60:
                give_chance = True
                reasoning_parts.append("Score close to threshold")
                confidence += 0.2
            
            # Basic skills check
            candidate_skills = [skill.lower() for skill in candidate_data.get("skills", [])]
            job_skills = [skill.lower() for skill in job_requirements.get("key_skills", [])]
            
            if candidate_skills and job_skills:
                skill_overlap = len(set(candidate_skills) & set(job_skills))
                if skill_overlap >= 2:
                    give_chance = True
                    reasoning_parts.append(f"Found {skill_overlap} matching skills")
                    confidence += 0.2
        
        # Final decision
        if not reasoning_parts:
            reasoning_parts.append("Insufficient qualifications for resume update opportunity")
            give_chance = False
            confidence = 0.2
        
        final_reasoning = "Rule-based evaluation: " + "; ".join(reasoning_parts) + "."
        
        return {
            "should_give_chance": give_chance,
            "reasoning": final_reasoning,
            "confidence": min(confidence, 1.0),
            "key_strengths": candidate_data.get("skills", [])[:3] if candidate_data.get("skills") else [],
            "improvement_areas": ["Resume formatting", "Keyword optimization", "Skills presentation"],
            "recommendation": "Focus on improving resume structure and highlighting relevant experience" if give_chance else "Consider gaining more relevant experience"
        }

    async def initiate_resume_update_flow(
        self, 
        db: Session, 
        application: Application, 
        current_score: float,
        scoring_context: Dict[str, float] = None
    ) -> bool:
        """
        Initiate the resume update flow for a candidate with score < 70
        Returns True if flow was initiated, False if rejected
        """
        try:
            # Check if already has an update request
            existing_request = db.query(ResumeUpdateRequest).filter_by(application_id=application.id).first()
            if existing_request:
                logger.warning(f"Resume update request already exists for application {application.id}")
                return False
            
            # Evaluate with LLM
            should_give_chance, reasoning, evaluation_details = await self.evaluate_candidate_with_llm(
                db, application, current_score
            )
            
            # Create resume update request record
            update_request = ResumeUpdateRequest(
                application_id=application.id,
                llm_evaluation_result=should_give_chance,
                llm_evaluation_reason=reasoning,
                status="llm_approved" if should_give_chance else "llm_rejected"
            )
            
            db.add(update_request)
            db.commit()
            db.refresh(update_request)
            
            if should_give_chance:
                # Update application status
                application.status = "resume_update_requested"
                db.commit()
                
                # Send first resume update email
                await self.send_resume_update_email(db, update_request, attempt_number=1)
                
                logger.info(f"Resume update flow initiated for application {application.id}")
                return True
            else:
                # Update application status to rejected
                application.status = "rejected"
                update_request.status = "llm_rejected"
                update_request.completed_at = datetime.utcnow()
                update_request.completion_reason = "LLM evaluation: insufficient potential"
                db.commit()
                
                logger.info(f"Application {application.id} rejected by LLM evaluation")
                return False
                
        except Exception as e:
            logger.error(f"Error initiating resume update flow for application {application.id}: {e}")
            db.rollback()
            return False

    async def send_resume_update_email(
        self, 
        db: Session, 
        update_request: ResumeUpdateRequest, 
        attempt_number: int
    ) -> bool:
        """Send resume update request email to candidate"""
        try:
            application = update_request.application
            job = application.job
            
            # Create email content
            subject = f"Opportunity to Update Your Application - {job.title}"
            
            # Calculate deadline (24 hours from now)
            deadline = datetime.now() + timedelta(hours=24)
            deadline_str = deadline.strftime("%B %d, %Y at %I:%M %p")
            
            # Create update history record
            update_history = ResumeUpdateHistory(
                update_request_id=update_request.id,
                attempt_number=attempt_number,
                email_sent_at=datetime.utcnow(),
                old_score=update_request.application.scores[-1].final_score if update_request.application.scores else 0
            )
            
            db.add(update_history)
            
            # Update request tracking
            update_request.update_attempts_count = attempt_number
            update_request.last_email_sent_at = datetime.utcnow()
            update_request.next_email_due_at = datetime.utcnow() + timedelta(hours=24)
            update_request.status = "email_sent"
            
            db.commit()
            
            # Email content
            body = f"""Dear {application.full_name},

Thank you for your interest in the {job.title} position at our company.

After reviewing your application, we believe you have potential for this role, but your resume could be improved to better showcase your qualifications. We would like to give you an opportunity to update your resume and resubmit it for consideration.

**What you can do:**
1. Visit our application portal using your reference number: {application.reference_number}
2. Upload an updated resume that better highlights:
   - Relevant skills and experience
   - Key achievements and accomplishments
   - Technical competencies
   - Educational background

**Deadline:** Please update your resume by {deadline_str}

**This is attempt {attempt_number} of {update_request.max_attempts}.**

To update your resume, please visit:
{settings.frontend_url}/update-resume/{application.reference_number}

If you have any questions, please don't hesitate to contact our HR team.

Best regards,
HR Team"""

            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2c5aa0;">Opportunity to Update Your Application</h2>
                    
                    <p>Dear <strong>{application.full_name}</strong>,</p>
                    
                    <p>Thank you for your interest in the <strong>{job.title}</strong> position at our company.</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #2c5aa0; margin: 20px 0;">
                        <p><strong>Good news!</strong> After reviewing your application, we believe you have potential for this role, but your resume could be improved to better showcase your qualifications.</p>
                    </div>
                    
                    <h3 style="color: #2c5aa0;">What you can do:</h3>
                    <ol>
                        <li>Visit our application portal using your reference number: <strong>{application.reference_number}</strong></li>
                        <li>Upload an updated resume that better highlights:
                            <ul>
                                <li>Relevant skills and experience</li>
                                <li>Key achievements and accomplishments</li>
                                <li>Technical competencies</li>
                                <li>Educational background</li>
                            </ul>
                        </li>
                    </ol>
                    
                    <div style="background-color: #fff3cd; padding: 15px; border: 1px solid #ffeaa7; border-radius: 5px; margin: 20px 0;">
                        <p><strong>⏰ Deadline:</strong> Please update your resume by <strong>{deadline_str}</strong></p>
                        <p><strong>📝 Attempt:</strong> This is attempt <strong>{attempt_number}</strong> of <strong>{update_request.max_attempts}</strong></p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.frontend_url}/update-resume/{application.reference_number}" 
                           style="background-color: #2c5aa0; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Update My Resume
                        </a>
                    </div>
                    
                    <p>If you have any questions, please don't hesitate to contact our HR team.</p>
                    
                    <p>Best regards,<br>
                    <strong>HR Team</strong></p>
                </div>
            </body>
            </html>
            """
            
            # Send email
            success = send_email(
                to_emails=[application.email],
                subject=subject,
                body=body,
                html_body=html_body
            )
            
            if success:
                logger.info(f"Resume update email sent successfully to {application.email} (attempt {attempt_number})")
                return True
            else:
                logger.error(f"Failed to send resume update email to {application.email}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending resume update email: {e}")
            db.rollback()
            return False

    async def process_resume_update(
        self, 
        db: Session, 
        application: Application, 
        new_resume_file_path: str, 
        new_resume_filename: str
    ) -> Dict[str, Any]:
        """Process updated resume and re-score the application"""
        try:
            # Get the update request
            update_request = db.query(ResumeUpdateRequest).filter_by(application_id=application.id).first()
            if not update_request:
                raise ValueError("No resume update request found for this application")
            
            # Get current update history
            current_history = db.query(ResumeUpdateHistory).filter(
                and_(
                    ResumeUpdateHistory.update_request_id == update_request.id,
                    ResumeUpdateHistory.attempt_number == update_request.update_attempts_count
                )
            ).first()
            
            if not current_history:
                raise ValueError("No current update history found")
            
            # Store old resume info
            old_resume_filename = application.resume_filename
            old_score = application.scores[-1].final_score if application.scores else 0
            
            # Update application with new resume
            application.resume_filename = new_resume_filename
            application.resume_path = new_resume_file_path
            
            # Parse new resume
            parsed_data = parse_resume(new_resume_file_path, new_resume_filename)
            
            # Update application with new parsed data
            application.parsed_skills = parsed_data.get('parsed_skills', [])
            application.parsed_experience = parsed_data.get('parsed_experience', [])
            application.parsed_education = parsed_data.get('parsed_education', [])
            application.parsed_certifications = parsed_data.get('parsed_certifications', [])
            
            db.commit()
            
            # Re-score the application
            new_score_record = await self.scoring_service.score_application(db, application)
            new_score = new_score_record.final_score
            
            # Update history record
            current_history.resume_updated = True
            current_history.resume_updated_at = datetime.utcnow()
            current_history.old_resume_filename = old_resume_filename
            current_history.new_resume_filename = new_resume_filename
            current_history.old_score = old_score
            current_history.new_score = new_score
            current_history.score_improvement = new_score - old_score
            current_history.new_scoring_details = new_score_record.scoring_details
            current_history.status = "rescored"
            
            # Check if threshold achieved
            if new_score >= self.shortlist_threshold:
                # Success! Candidate achieved the threshold
                current_history.status = "threshold_achieved"
                update_request.status = "completed_success"
                update_request.final_score_achieved = new_score
                update_request.completion_reason = f"Achieved score of {new_score:.1f} (≥{self.shortlist_threshold})"
                update_request.completed_at = datetime.utcnow()
                
                # Update application status to selected (will trigger interview flow)
                application.status = "selected"
                
                db.commit()
                
                # Trigger selection flow
                from .interview_service import InterviewService
                interview_service = InterviewService()
                await interview_service.trigger_selection_flow(db, application)
                
                logger.info(f"Application {application.id} achieved threshold with score {new_score:.1f}")
                
                return {
                    "success": True,
                    "threshold_achieved": True,
                    "old_score": old_score,
                    "new_score": new_score,
                    "improvement": new_score - old_score,
                    "message": f"Congratulations! Your updated resume achieved a score of {new_score:.1f}, which meets our threshold. You will be contacted for the next steps."
                }
            else:
                # Still below threshold, check if more attempts available
                if update_request.update_attempts_count < update_request.max_attempts:
                    # More attempts available, schedule next email
                    update_request.status = "llm_approved"  # Ready for next attempt
                    update_request.next_email_due_at = datetime.utcnow() + timedelta(hours=24)  # Schedule next email in 24 hours
                    
                    # Keep application in resume_update_requested status (scoring service may have changed it)
                    application.status = "resume_update_requested"
                    
                    db.commit()
                    
                    logger.info(f"Application {application.id} improved from {old_score:.1f} to {new_score:.1f} but still below threshold. Next email scheduled for {update_request.next_email_due_at}")
                    
                    return {
                        "success": True,
                        "threshold_achieved": False,
                        "old_score": old_score,
                        "new_score": new_score,
                        "improvement": new_score - old_score,
                        "attempts_remaining": update_request.max_attempts - update_request.update_attempts_count,
                        "message": f"Your score improved from {old_score:.1f} to {new_score:.1f}, but hasn't reached our threshold of {self.shortlist_threshold} yet. You have {update_request.max_attempts - update_request.update_attempts_count} more attempt(s). You will receive another opportunity email within 24 hours."
                    }
                else:
                    # No more attempts, final rejection
                    update_request.status = "completed_failure"
                    update_request.final_score_achieved = new_score
                    update_request.completion_reason = f"Max attempts reached. Final score: {new_score:.1f} (< {self.shortlist_threshold})"
                    update_request.completed_at = datetime.utcnow()
                    
                    application.status = "rejected"
                    db.commit()
                    
                    logger.info(f"Application {application.id} exhausted all attempts. Final score: {new_score:.1f}")
                    
                    return {
                        "success": True,
                        "threshold_achieved": False,
                        "old_score": old_score,
                        "new_score": new_score,
                        "improvement": new_score - old_score,
                        "attempts_remaining": 0,
                        "final_rejection": True,
                        "message": f"Your score improved from {old_score:.1f} to {new_score:.1f}, but unfortunately hasn't reached our threshold of {self.shortlist_threshold}. You have used all available attempts."
                    }
            
        except Exception as e:
            logger.error(f"Error processing resume update for application {application.id}: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "message": "An error occurred while processing your resume update. Please try again or contact HR."
            }

    async def check_and_send_scheduled_emails(self, db: Session) -> int:
        """
        Check for scheduled resume update emails and send them
        This should be called by a background scheduler every hour
        """
        try:
            # Find update requests that need to send next email
            now = datetime.utcnow()
            
            pending_requests = db.query(ResumeUpdateRequest).filter(
                and_(
                    ResumeUpdateRequest.status == "llm_approved",
                    ResumeUpdateRequest.update_attempts_count < ResumeUpdateRequest.max_attempts,
                    ResumeUpdateRequest.next_email_due_at <= now
                )
            ).all()
            
            emails_sent = 0
            
            for request in pending_requests:
                next_attempt = request.update_attempts_count + 1
                
                if next_attempt <= request.max_attempts:
                    success = await self.send_resume_update_email(db, request, next_attempt)
                    if success:
                        emails_sent += 1
                        logger.info(f"Scheduled email sent for application {request.application_id}, attempt {next_attempt}")
                else:
                    # Max attempts reached, mark as completed failure
                    request.status = "completed_failure"
                    request.completion_reason = "Max attempts reached without resume update"
                    request.completed_at = datetime.utcnow()
                    request.application.status = "rejected"
                    db.commit()
                    logger.info(f"Application {request.application_id} marked as rejected - max attempts reached")
            
            return emails_sent
            
        except Exception as e:
            logger.error(f"Error in scheduled email check: {e}")
            return 0

# Create service instance
resume_update_service = ResumeUpdateService()
