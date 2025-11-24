from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from ..models.job import Job, JobRequirement
from ..models.application import Application, ApplicationScore
from ..config import settings
from ..services.llm_service import LLMService
import logging

logger = logging.getLogger(__name__)

class ScoringService:
    def __init__(self):
        self.match_weight = settings.match_score_weight
        self.ats_weight = settings.ats_score_weight
        self.shortlist_threshold = settings.shortlist_threshold
        self.requalify_threshold = settings.requalify_threshold
        self.llm_service = LLMService()
    
    def calculate_match_score(self, job: Job, application: Application) -> Dict[str, float]:
        """Calculate job-candidate match score"""
        scores = {
            'skills_match': 0.0,
            'experience_match': 0.0,
            'education_match': 0.0,
            'certification_match': 0.0
        }
        
        # Helper function to ensure we have a list
        def ensure_list(data):
            if isinstance(data, str):
                import json
                try:
                    return json.loads(data)
                except:
                    return []
            return data if data is not None else []
        
        # Skills matching
        job_skills_raw = ensure_list(job.key_skills)
        candidate_skills_raw = ensure_list(application.parsed_skills)
        
        if job_skills_raw and candidate_skills_raw:
            job_skills = [skill.lower() for skill in job_skills_raw]
            candidate_skills = [skill.lower() for skill in candidate_skills_raw]
            
            matched_skills = set(job_skills) & set(candidate_skills)
            if job_skills:
                scores['skills_match'] = (len(matched_skills) / len(job_skills)) * 100
        
        # Experience matching (simplified - can be enhanced)
        experience_data = ensure_list(application.parsed_experience)
        if experience_data:
            if len(experience_data) >= 2:
                scores['experience_match'] = 80.0
            elif len(experience_data) >= 1:
                scores['experience_match'] = 60.0
            else:
                scores['experience_match'] = 20.0
        
        # Education matching
        education_data = ensure_list(application.parsed_education)
        if education_data:
            # Handle both string and dict formats
            education_strings = []
            for edu in education_data:
                if isinstance(edu, dict):
                    education_strings.append(edu.get('degree', '').lower())
                else:
                    education_strings.append(str(edu).lower())
            
            if any('master' in edu_str for edu_str in education_strings):
                scores['education_match'] = 90.0
            elif any('bachelor' in edu_str for edu_str in education_strings):
                scores['education_match'] = 70.0
            else:
                scores['education_match'] = 50.0
        
        # Certification matching
        job_certs_raw = ensure_list(job.certifications)
        candidate_certs_raw = ensure_list(application.parsed_certifications)
        
        if job_certs_raw and candidate_certs_raw:
            job_certs = [cert.lower() for cert in job_certs_raw]
            candidate_certs = [cert.lower() for cert in candidate_certs_raw]
            
            matched_certs = set(job_certs) & set(candidate_certs)
            if job_certs:
                scores['certification_match'] = (len(matched_certs) / len(job_certs)) * 100
        
        return scores
    
    def calculate_ats_score_breakdown(self, parsed_data: Dict[str, Any], filename: str) -> Dict[str, float]:
        """Calculate detailed ATS score breakdown"""
        scores = {
            'ats_format_score': 0.0,
            'ats_keywords_score': 0.0,
            'ats_structure_score': 0.0
        }
        
        # Format score
        if filename.lower().endswith(('.pdf', '.docx')):
            scores['ats_format_score'] = 100.0
        else:
            scores['ats_format_score'] = 30.0
        
        # Keywords score (based on extracted skills)
        if parsed_data.get('parsed_skills'):
            skill_count = len(parsed_data['parsed_skills'])
            scores['ats_keywords_score'] = min(skill_count * 10, 100.0)
        
        # Structure score (based on sections found)
        structure_score = 0.0
        if parsed_data.get('parsed_experience'):
            structure_score += 40.0
        if parsed_data.get('parsed_education'):
            structure_score += 30.0
        if parsed_data.get('parsed_skills'):
            structure_score += 30.0
        
        scores['ats_structure_score'] = structure_score
        
        return scores
    
    def calculate_final_score(self, match_scores: Dict[str, float], ats_scores: Dict[str, float]) -> float:
        """Calculate final weighted score"""
        # Calculate average match score
        match_values = [score for score in match_scores.values() if score > 0]
        avg_match_score = sum(match_values) / len(match_values) if match_values else 0.0
        
        # Calculate average ATS score
        ats_values = list(ats_scores.values())
        avg_ats_score = sum(ats_values) / len(ats_values) if ats_values else 0.0
        
        # Weighted final score
        final_score = (avg_match_score * self.match_weight) + (avg_ats_score * self.ats_weight)
        return round(final_score, 2)
    
    def determine_candidate_status(self, final_score: float) -> Tuple[str, str]:
        """Determine candidate status based on score"""
        if final_score >= self.shortlist_threshold:
            return "auto_selected", "selected"  # Auto-trigger selection flow for ≥70
        else:
            # Score < 70: Trigger LLM evaluation for potential resume update flow
            return "llm_evaluation_needed", "pending_llm_evaluation"
    
    def generate_ai_feedback(self, job: Job, application: Application, scores: Dict[str, float]) -> str:
        """Generate AI feedback for the candidate (rule-based fallback)"""
        feedback_parts = []
        
        # Skills feedback
        if scores.get('skills_match', 0) >= 70:
            feedback_parts.append("Strong skill match with job requirements.")
        elif scores.get('skills_match', 0) >= 40:
            feedback_parts.append("Good skill alignment with some areas for improvement.")
        else:
            feedback_parts.append("Limited skill match with job requirements.")
        
        # Experience feedback
        if scores.get('experience_match', 0) >= 70:
            feedback_parts.append("Relevant work experience aligns well with the role.")
        elif scores.get('experience_match', 0) >= 40:
            feedback_parts.append("Some relevant experience, but could benefit from more exposure.")
        else:
            feedback_parts.append("Limited relevant work experience for this role.")
        
        # ATS feedback
        avg_ats = (scores.get('ats_format_score', 0) + scores.get('ats_keywords_score', 0) + scores.get('ats_structure_score', 0)) / 3
        if avg_ats >= 70:
            feedback_parts.append("Resume is well-formatted for ATS systems.")
        else:
            feedback_parts.append("Resume could be better optimized for ATS systems.")
        
        return " ".join(feedback_parts)
    
    async def generate_llm_score_explanation(
        self, 
        job: Job, 
        application: Application, 
        match_score: float,
        ats_score: float,
        final_score: float,
        match_scores: Dict[str, float],
        ats_scores: Dict[str, float]
    ) -> str:
        """Generate detailed LLM explanation for why the candidate received these scores"""
        try:
            # Helper function to ensure we have a list
            def ensure_list(data):
                if isinstance(data, str):
                    try:
                        return json.loads(data)
                    except:
                        return []
                return data if data is not None else []
            
            # Prepare context data
            job_skills = ensure_list(job.key_skills)
            candidate_skills = ensure_list(application.parsed_skills)
            candidate_experience = ensure_list(application.parsed_experience)
            candidate_education = ensure_list(application.parsed_education)
            candidate_certifications = ensure_list(application.parsed_certifications)
            
            # Calculate matched and missing skills
            job_skills_lower = [skill.lower() for skill in job_skills] if job_skills else []
            candidate_skills_lower = [skill.lower() for skill in candidate_skills] if candidate_skills else []
            matched_skills = [skill for skill in job_skills if skill.lower() in candidate_skills_lower]
            missing_skills = [skill for skill in job_skills if skill.lower() not in candidate_skills_lower]
            
            # Skip resume text extraction for speed - we already have parsed data
            # Resume text extraction is slow and we have all the key info from parsing
            resume_text = ""
            
            # Format experience details (more concise for speed)
            experience_details = ""
            if candidate_experience:
                for i, exp in enumerate(candidate_experience[:2], 1):  # Limit to first 2 experiences only
                    if isinstance(exp, dict):
                        exp_str = f"{exp.get('title', 'N/A')}@{exp.get('company', 'N/A')}"
                        if exp.get('duration'):
                            exp_str += f"({exp.get('duration')})"
                        experience_details += f" {i}.{exp_str}"
                    else:
                        experience_details += f" {i}.{str(exp)[:50]}"  # Truncate long strings
            
            # Format education details (more concise)
            education_details = ""
            if candidate_education:
                for i, edu in enumerate(candidate_education[:2], 1):  # Limit to first 2 education entries
                    if isinstance(edu, dict):
                        edu_str = f"{edu.get('degree', 'N/A')}"
                        if edu.get('university'):
                            edu_str += f"@{edu.get('university')}"
                        education_details += f" {i}.{edu_str}"
                    else:
                        education_details += f" {i}.{str(edu)[:50]}"  # Truncate long strings
            
            # Prepare default messages for experience and education (not used in current prompt but kept for compatibility)
            no_experience_msg = "No experience details extracted"
            no_education_msg = "No education details extracted"
            
            # Build optimized prompt for faster LLM processing
            # Reduced verbosity while maintaining quality
            prompt = f"""Analyze candidate {application.full_name} for {job.title} role.

JOB REQUIREMENTS:
- Skills: {', '.join(job_skills[:8]) if job_skills else 'Not specified'}
- Experience: {job.required_experience if hasattr(job, 'required_experience') and job.required_experience else 'Not specified'}

CANDIDATE PROFILE:
- Skills: {', '.join(candidate_skills[:12]) if candidate_skills else 'None'}
- Matched: {', '.join(matched_skills[:8]) if matched_skills else 'NONE'}
- Missing: {', '.join(missing_skills[:8]) if missing_skills else 'NONE'}
- Experience: {len(candidate_experience)} entries{experience_details[:150] if experience_details else ''}
- Education: {len(candidate_education)} entries{education_details[:150] if education_details else ''}

SCORES: Overall {final_score}% | Match {match_score}% (Skills:{match_scores.get('skills_match', 0):.0f}% Exp:{match_scores.get('experience_match', 0):.0f}% Edu:{match_scores.get('education_match', 0):.0f}%) | ATS {ats_score}% (Format:{ats_scores.get('ats_format_score', 0):.0f}% Keywords:{ats_scores.get('ats_keywords_score', 0):.0f}% Structure:{ats_scores.get('ats_structure_score', 0):.0f}%)

Provide a concise but detailed explanation (250-400 words) covering:
1. Overall score meaning ({final_score}%) - strong/moderate/weak candidate?
2. Match analysis - skill gaps, experience fit, education alignment
3. ATS analysis - format quality, keyword optimization
4. Top 3-4 strengths
5. Top 3-4 improvement areas  
6. Recommendation

Be specific and reference actual data."""

            # Shorter system message for faster processing
            messages = [
                {
                    "role": "system", 
                    "content": "Expert HR analyst. Provide detailed, specific candidate analysis. Be concise but thorough."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            logger.info(f"Generating detailed LLM score explanation for application {application.id} - candidate: {application.full_name}")
            # Use a very long timeout (30 minutes) - user wants explanation no matter how long it takes
            from ..config import settings
            # Use a very long timeout to allow for slow LLM responses
            explanation_timeout = max(1800, settings.llm_timeout_seconds)  # At least 30 minutes (1800 seconds)
            logger.info(f"Using timeout of {explanation_timeout} seconds ({explanation_timeout/60:.1f} minutes) for LLM explanation")
            explanation = await self.llm_service._chat_ollama(
                messages, 
                temperature=0.3,  # Lower temperature for faster, more focused responses
                max_tokens=800,  # Reduced from 1200 to speed up generation (still enough for detailed explanation)
                timeout=explanation_timeout
            )
            
            if not explanation or len(explanation.strip()) < 100:
                # If explanation is too short, it might have failed
                logger.warning(f"LLM explanation too short ({len(explanation) if explanation else 0} chars), might have failed")
                raise Exception("LLM returned insufficient explanation")
            
            return explanation.strip()
            
        except Exception as e:
            error_msg = str(e) if str(e) else "Unknown error"
            error_type = type(e).__name__
            logger.error(f"Error generating LLM score explanation for application {application.id}: {error_type}: {error_msg}", exc_info=True)
            # Return None instead of error message - scoring will continue without explanation
            # The error is already logged for debugging
            model_name = getattr(self.llm_service, 'ollama_model', 'unknown')
            logger.warning(f"LLM explanation failed for application {application.id}. Model: {model_name}. Error: {error_type}: {error_msg}")
            return None
    
    async def score_application(self, db: Session, application: Application) -> ApplicationScore:
        """Score an application and return the score object"""
        try:
            # Get job details
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if not job:
                raise ValueError(f"Job not found for application {application.id}")
            
            # Calculate match scores
            match_scores = self.calculate_match_score(job, application)
            
            # Calculate ATS scores
            parsed_data = {
                'parsed_skills': application.parsed_skills,
                'parsed_experience': application.parsed_experience,
                'parsed_education': application.parsed_education,
                'parsed_certifications': application.parsed_certifications
            }
            ats_scores = self.calculate_ats_score_breakdown(parsed_data, application.resume_filename)
            
            # Calculate final score
            match_score = sum(score for score in match_scores.values() if score > 0) / len([s for s in match_scores.values() if s > 0]) if any(match_scores.values()) else 0
            ats_score = sum(ats_scores.values()) / len(ats_scores) if ats_scores else 0
            final_score = self.calculate_final_score(match_scores, ats_scores)
            
            # Generate feedback (rule-based for quick summary)
            all_scores = {**match_scores, **ats_scores}
            ai_feedback = self.generate_ai_feedback(job, application, all_scores)
            
            # Generate detailed LLM explanation for why candidate got these scores
            # User wants this to complete no matter how long it takes
            # We'll run it synchronously with a very long timeout
            import asyncio
            score_explanation = None
            try:
                logger.info(f"🚀 Starting LLM explanation generation for application {application.id} (this may take 10-30 minutes, please be patient)...")
                from ..config import settings
                
                # Generate explanation with a very long timeout (30 minutes) - user wants it no matter how long
                # Use the full timeout from settings, but ensure it's at least 30 minutes
                explanation_timeout = max(1800, settings.llm_timeout_seconds)  # At least 30 minutes (1800 seconds)
                logger.info(f"⏱️  Using timeout of {explanation_timeout} seconds ({explanation_timeout/60:.1f} minutes) for LLM explanation")
                
                score_explanation = await self.generate_llm_score_explanation(
                    job=job,
                    application=application,
                    match_score=match_score,
                    ats_score=ats_score,
                    final_score=final_score,
                    match_scores=match_scores,
                    ats_scores=ats_scores
                )
                
                if score_explanation:
                    logger.info(f"✅ LLM explanation generated successfully for application {application.id} ({len(score_explanation)} chars)")
                else:
                    logger.warning(f"⚠️  LLM explanation returned None for application {application.id}")
                    
            except asyncio.TimeoutError:
                logger.error(f"⏱️  LLM explanation timed out after {explanation_timeout} seconds for application {application.id}")
                # Try to generate a basic explanation as fallback
                score_explanation = f"Detailed explanation generation timed out after {explanation_timeout/60:.1f} minutes. Basic analysis: Final score {final_score}% indicates {'strong' if final_score >= 70 else 'moderate' if final_score >= 50 else 'weak'} candidate match. Match score {match_score}% reflects skills/experience alignment. ATS score {ats_score}% indicates resume format quality."
            except Exception as llm_error:
                logger.error(f"❌ Failed to generate LLM score explanation for application {application.id}: {llm_error}", exc_info=True)
                # Generate a basic fallback explanation
                score_explanation = f"Detailed explanation generation failed. Basic analysis: Final score {final_score}% indicates {'strong' if final_score >= 70 else 'moderate' if final_score >= 50 else 'weak'} candidate match. Match score {match_score}% reflects skills/experience alignment. ATS score {ats_score}% indicates resume format quality."
            
            # Create score record
            application_score = ApplicationScore(
                application_id=application.id,
                match_score=match_score,
                ats_score=ats_score,
                final_score=final_score,
                skills_match=match_scores.get('skills_match'),
                experience_match=match_scores.get('experience_match'),
                education_match=match_scores.get('education_match'),
                certification_match=match_scores.get('certification_match'),
                ats_format_score=ats_scores.get('ats_format_score'),
                ats_keywords_score=ats_scores.get('ats_keywords_score'),
                ats_structure_score=ats_scores.get('ats_structure_score'),
                scoring_details=all_scores,
                ai_feedback=ai_feedback,
                score_explanation=score_explanation
            )
            
            db.add(application_score)
            db.commit()
            db.refresh(application_score)
            
            # Update application status based on score
            decision, status = self.determine_candidate_status(final_score)
            
            # Handle different scoring outcomes
            if decision == "auto_selected":
                # Score ≥ 70: Proceed with normal selection flow
                application.status = status
                db.commit()
                
                from .interview_service import InterviewService
                interview_service = InterviewService()
                await interview_service.trigger_selection_flow(db, application)
                
            elif decision == "llm_evaluation_needed":
                # Score < 70: Trigger LLM evaluation and potential resume update flow
                try:
                    from .resume_update_service import resume_update_service
                    
                    # Check if this is a re-scoring (already has update request)
                    from ..models.resume_update_tracking import ResumeUpdateRequest
                    existing_request = db.query(ResumeUpdateRequest).filter_by(application_id=application.id).first()
                    
                    if existing_request:
                        # This is a re-scoring after resume update, don't create new request
                        application.status = status
                        db.commit()
                    else:
                        # Initial scoring, initiate LLM evaluation and potential resume update flow
                        # Pass detailed scoring information for better LLM evaluation
                        scoring_context = {
                            "final_score": final_score,
                            "match_score": match_score,
                            "ats_score": ats_score,
                            "skills_match": match_scores.get('skills_match', 0),
                            "experience_match": match_scores.get('experience_match', 0),
                            "education_match": match_scores.get('education_match', 0),
                            "certification_match": match_scores.get('certification_match', 0)
                        }
                        try:
                            flow_initiated = await resume_update_service.initiate_resume_update_flow(
                                db, application, final_score, scoring_context
                            )
                            
                            if not flow_initiated:
                                # LLM rejected or flow failed, set to rejected
                                application.status = "rejected"
                                db.commit()
                        except Exception as flow_error:
                            # Resume update flow failed, but don't break scoring
                            logger.warning(f"Resume update flow failed for application {application.id}: {flow_error}")
                            # Set status to under_review as fallback
                            application.status = "under_review"
                            db.commit()
                except Exception as e:
                    # If resume update service import or query fails, don't break scoring
                    logger.warning(f"Error in resume update flow for application {application.id}: {e}")
                    application.status = status
                    db.commit()
            else:
                # Other statuses (under_review, rejected)
                application.status = status
                db.commit()
            
            return application_score
            
        except Exception as e:
            logger.error(f"Error scoring application {application.id}: {e}")
            db.rollback()
            raise
