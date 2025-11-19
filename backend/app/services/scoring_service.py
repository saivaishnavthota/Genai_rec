from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from ..models.job import Job, JobRequirement
from ..models.application import Application, ApplicationScore
from ..config import settings
from ..services.llm_service import LLMService
import logging
import json

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
            
            # Extract resume text if available
            resume_text = ""
            if application.resume_path:
                try:
                    from ..utils.resume_parser import extract_text_from_pdf, extract_text_from_docx, extract_text_from_doc
                    import os
                    if os.path.exists(application.resume_path):
                        if application.resume_filename.lower().endswith('.pdf'):
                            resume_text = extract_text_from_pdf(application.resume_path)
                        elif application.resume_filename.lower().endswith('.docx'):
                            resume_text = extract_text_from_docx(application.resume_path)
                        elif application.resume_filename.lower().endswith('.doc'):
                            resume_text = extract_text_from_doc(application.resume_path)
                        # Limit resume text to first 2000 chars to avoid token limits
                        resume_text = resume_text[:2000] if resume_text else ""
                except Exception as e:
                    logger.warning(f"Could not extract resume text: {e}")
                    resume_text = ""
            
            # Format experience details
            newline = "\n"
            experience_details = ""
            if candidate_experience:
                for i, exp in enumerate(candidate_experience[:3], 1):  # Limit to first 3 experiences
                    if isinstance(exp, dict):
                        exp_str = f"{exp.get('title', 'N/A')} at {exp.get('company', 'N/A')}"
                        if exp.get('duration'):
                            exp_str += f" ({exp.get('duration')})"
                        experience_details += f"{newline}  {i}. {exp_str}"
                    else:
                        experience_details += f"{newline}  {i}. {str(exp)}"
            
            # Format education details
            education_details = ""
            if candidate_education:
                for i, edu in enumerate(candidate_education[:3], 1):  # Limit to first 3 education entries
                    if isinstance(edu, dict):
                        edu_str = f"{edu.get('degree', 'N/A')}"
                        if edu.get('university'):
                            edu_str += f" from {edu.get('university')}"
                        education_details += f"{newline}  {i}. {edu_str}"
                    else:
                        education_details += f"{newline}  {i}. {str(edu)}"
            
            # Prepare default messages for experience and education
            no_experience_msg = f"{newline}  No experience details extracted"
            no_education_msg = f"{newline}  No education details extracted"
            
            # Build comprehensive prompt for LLM
            prompt = f"""You are an expert HR analyst and recruitment consultant. Analyze this candidate's application and provide a VERY DETAILED, comprehensive explanation of why they received these specific scores.

=== JOB REQUIREMENTS ===
Position: {job.title}
Job Description: {job.description[:800] if job.description else 'No description provided'}
Required Skills: {', '.join(job_skills) if job_skills else 'Not specified'}
Required Experience: {job.required_experience if hasattr(job, 'required_experience') and job.required_experience else 'Not specified'}
Department: {job.department if hasattr(job, 'department') and job.department else 'Not specified'}
Location: {job.location if hasattr(job, 'location') and job.location else 'Not specified'}

=== CANDIDATE PROFILE ===
Name: {application.full_name}
Email: {application.email}
Phone: {application.phone or 'Not provided'}

CANDIDATE SKILLS FOUND IN RESUME:
{', '.join(candidate_skills) if candidate_skills else 'No skills extracted from resume'}

SKILL MATCHING ANALYSIS:
- Skills that MATCH job requirements: {', '.join(matched_skills) if matched_skills else 'NONE'}
- Skills REQUIRED but MISSING from candidate: {', '.join(missing_skills) if missing_skills else 'NONE - All required skills present'}
- Candidate's additional skills (not in job requirements): {', '.join([s for s in candidate_skills if s.lower() not in job_skills_lower]) if candidate_skills else 'None'}

CANDIDATE EXPERIENCE:
Number of experience entries: {len(candidate_experience) if candidate_experience else 0}
Experience details:{experience_details if experience_details else no_experience_msg}

CANDIDATE EDUCATION:
Number of education entries: {len(candidate_education) if candidate_education else 0}
Education details:{education_details if education_details else no_education_msg}

CANDIDATE CERTIFICATIONS:
{', '.join(candidate_certifications) if candidate_certifications else 'No certifications found'}

RESUME CONTENT (First 2000 characters):
{resume_text if resume_text else 'Resume text not available for analysis'}

COVER LETTER:
{application.cover_letter[:500] if application.cover_letter else 'No cover letter provided'}

=== SCORING BREAKDOWN ===
Overall AI Score: {final_score}% (Weighted combination of Match Score and ATS Score)

MATCH SCORE: {match_score}% (How well candidate matches job requirements)
  - Skills Match: {match_scores.get('skills_match', 0):.1f}% ({len(matched_skills)}/{len(job_skills)} required skills matched)
  - Experience Match: {match_scores.get('experience_match', 0):.1f}% ({len(candidate_experience)} experience entries found)
  - Education Match: {match_scores.get('education_match', 0):.1f}% ({len(candidate_education)} education entries found)
  - Certification Match: {match_scores.get('certification_match', 0):.1f}% ({len(candidate_certifications)} certifications found)

ATS SCORE: {ats_score}% (Resume format and ATS compatibility)
  - Format Score: {ats_scores.get('ats_format_score', 0):.1f}% (File format: {application.resume_filename.split('.')[-1].upper() if application.resume_filename else 'Unknown'})
  - Keywords Score: {ats_scores.get('ats_keywords_score', 0):.1f}% ({len(candidate_skills)} skills/keywords found)
  - Structure Score: {ats_scores.get('ats_structure_score', 0):.1f}% (Resume sections completeness)

=== YOUR TASK ===
Provide a COMPREHENSIVE, DETAILED explanation (minimum 4-5 paragraphs, 500-800 words) that covers:

1. **Overall Score Analysis**: Explain why this candidate received {final_score}% overall. What does this score mean in practical terms? Is this a strong candidate, moderate, or weak? Why?

2. **Match Score Deep Dive ({match_score}%)**: 
   - Skills Analysis: Which specific skills match and why that matters. Which missing skills are critical gaps? How do the candidate's additional skills (if any) add value?
   - Experience Analysis: Detailed assessment of their experience - is it relevant? How many years? Does it align with job requirements? What specific roles/responsibilities are relevant?
   - Education Analysis: Does their education match requirements? Is the level appropriate? Any notable institutions or degrees?
   - Certification Analysis: Are required certifications present? How do certifications impact this role?

3. **ATS Score Deep Dive ({ats_score}%)**:
   - Format Analysis: Why did they get this format score? Is the resume format ATS-friendly?
   - Keywords Analysis: How well did they optimize for keywords? What keywords are present/missing?
   - Structure Analysis: Is the resume well-structured? Are all sections present and properly formatted?

4. **Candidate Strengths**: List 3-5 specific strengths this candidate brings to the role. Be specific and reference actual data from their profile.

5. **Areas for Improvement**: List 3-5 specific areas where the candidate could improve. Be constructive and actionable. What would make them a stronger fit?

6. **Final Assessment**: Overall recommendation - is this candidate suitable? What role would they be best suited for? Any concerns or red flags?

IMPORTANT: 
- Be VERY specific and reference actual data from the candidate's profile
- Use the candidate's name, specific skills, experience details in your explanation
- Make this explanation UNIQUE to this candidate - it should not be generic
- Write in a professional but conversational tone
- Be thorough and detailed - this is for HR decision-making"""

            messages = [
                {
                    "role": "system", 
                    "content": "You are an expert HR analyst and recruitment consultant with 15+ years of experience in talent acquisition, candidate evaluation, and hiring decisions. You provide detailed, insightful, and actionable analysis of candidates. Your explanations are comprehensive, specific, and tailored to each individual candidate. You never use generic templates - every explanation is unique based on the candidate's actual profile."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            logger.info(f"Generating detailed LLM score explanation for application {application.id} - candidate: {application.full_name}")
            # Increased max_tokens to get longer, more detailed explanations
            # Use a longer timeout for this operation since it's generating a detailed response
            from ..config import settings
            explanation = await self.llm_service._chat_ollama(
                messages, 
                temperature=0.4, 
                max_tokens=1200,
                timeout=settings.llm_timeout_seconds
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
            # Don't fallback to rule-based - return a message indicating LLM explanation failed
            # This way we can see the issue and fix it
            model_name = getattr(self.llm_service, 'ollama_model', 'unknown')
            return f"[LLM Explanation Generation Failed: {error_type}: {error_msg}. Please check logs and ensure Ollama is running with model '{model_name}'. If the model is not installed, run: ollama pull {model_name}]"
    
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
            # Wrap in try-catch so LLM failures don't break the entire scoring process
            score_explanation = None
            try:
                score_explanation = await self.generate_llm_score_explanation(
                    job=job,
                    application=application,
                    match_score=match_score,
                    ats_score=ats_score,
                    final_score=final_score,
                    match_scores=match_scores,
                    ats_scores=ats_scores
                )
            except Exception as llm_error:
                logger.warning(f"Failed to generate LLM score explanation for application {application.id}: {llm_error}")
                # Continue without explanation - scoring can still succeed
                score_explanation = None
            
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
                    flow_initiated = await resume_update_service.initiate_resume_update_flow(
                        db, application, final_score, scoring_context
                    )
                    
                    if not flow_initiated:
                        # LLM rejected or flow failed, set to rejected
                        application.status = "rejected"
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
