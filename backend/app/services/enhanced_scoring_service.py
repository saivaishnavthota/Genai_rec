"""
Enhanced Scoring Service with improved LLM prompts and semantic matching
"""

from typing import Dict, List, Any, Tuple
from sqlalchemy.orm import Session
from ..models.job import Job, JobRequirement
from ..models.application import Application, ApplicationScore
from ..config import settings
from ..services.llm_service import LLMService
from ..utils.enhanced_resume_parser import parse_resume_enhanced
import logging
import json

logger = logging.getLogger(__name__)


class EnhancedScoringService:
    """
    Enhanced scoring service with:
    1. Better skill matching (semantic + keyword)
    2. Improved LLM prompts for scoring
    3. More detailed scoring breakdown
    4. Context-aware evaluation
    """
    
    def __init__(self):
        self.match_weight = settings.match_score_weight
        self.ats_weight = settings.ats_score_weight
        self.shortlist_threshold = settings.shortlist_threshold
        self.requalify_threshold = settings.requalify_threshold
        self.llm_service = LLMService()
    
    def calculate_semantic_skill_match(
        self, 
        job_skills: List[str], 
        candidate_skills: List[str]
    ) -> Tuple[float, List[str], List[str], List[str]]:
        """
        Calculate skill match with semantic understanding
        Returns: (match_score, matched_skills, missing_skills, extra_skills)
        """
        if not job_skills:
            return 100.0, [], [], candidate_skills
        
        if not candidate_skills:
            return 0.0, [], job_skills, []
        
        # Normalize skills
        job_skills_lower = {skill.lower().strip() for skill in job_skills}
        candidate_skills_lower = {skill.lower().strip() for skill in candidate_skills}
        
        # Exact matches
        exact_matches = job_skills_lower & candidate_skills_lower
        
        # Semantic matches (similar technologies)
        semantic_map = {
            'react': ['reactjs', 'react.js', 'react native'],
            'node': ['nodejs', 'node.js'],
            'python': ['python3', 'python2'],
            'javascript': ['js', 'ecmascript', 'es6', 'es2015'],
            'typescript': ['ts'],
            'postgresql': ['postgres', 'psql'],
            'mongodb': ['mongo'],
            'aws': ['amazon web services'],
            'gcp': ['google cloud', 'google cloud platform'],
            'azure': ['microsoft azure'],
            'docker': ['containerization'],
            'kubernetes': ['k8s', 'container orchestration'],
            'machine learning': ['ml', 'ai', 'artificial intelligence'],
            'deep learning': ['neural networks', 'dl'],
        }
        
        semantic_matches = set()
        for job_skill in job_skills_lower:
            if job_skill in exact_matches:
                continue
            
            # Check if job skill has semantic equivalents in candidate skills
            for key, equivalents in semantic_map.items():
                if job_skill == key or job_skill in equivalents:
                    # Check if any equivalent is in candidate skills
                    for equiv in [key] + equivalents:
                        if equiv in candidate_skills_lower:
                            semantic_matches.add(job_skill)
                            break
        
        # Calculate match score
        total_matches = len(exact_matches) + len(semantic_matches)
        match_score = (total_matches / len(job_skills_lower)) * 100 if job_skills_lower else 0
        
        # Identify matched, missing, and extra skills
        matched_skills = list(exact_matches | semantic_matches)
        missing_skills = list(job_skills_lower - exact_matches - semantic_matches)
        extra_skills = list(candidate_skills_lower - job_skills_lower)
        
        return match_score, matched_skills, missing_skills, extra_skills
    
    def calculate_experience_match(
        self, 
        job: Job, 
        candidate_experience: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate experience match with detailed analysis
        """
        score_data = {
            'score': 0.0,
            'years_of_experience': 0,
            'relevant_roles': 0,
            'analysis': ''
        }
        
        if not candidate_experience:
            score_data['analysis'] = "No work experience found in resume"
            return score_data
        
        # Count years of experience (rough estimate)
        years = len(candidate_experience)
        score_data['years_of_experience'] = years
        
        # Count relevant roles (based on job title similarity)
        job_title_lower = job.title.lower()
        job_keywords = set(job_title_lower.split())
        
        relevant_count = 0
        for exp in candidate_experience:
            exp_title = exp.get('title', '').lower()
            exp_keywords = set(exp_title.split())
            
            # Check for keyword overlap
            if job_keywords & exp_keywords:
                relevant_count += 1
        
        score_data['relevant_roles'] = relevant_count
        
        # Calculate score
        if years >= 5:
            score_data['score'] = 90.0
        elif years >= 3:
            score_data['score'] = 75.0
        elif years >= 1:
            score_data['score'] = 60.0
        else:
            score_data['score'] = 40.0
        
        # Boost score if has relevant roles
        if relevant_count > 0:
            score_data['score'] = min(score_data['score'] + (relevant_count * 10), 100.0)
        
        score_data['analysis'] = f"{years} years of experience with {relevant_count} relevant roles"
        
        return score_data
    
    def calculate_education_match(
        self, 
        job: Job, 
        candidate_education: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculate education match with detailed analysis
        """
        score_data = {
            'score': 0.0,
            'highest_degree': '',
            'relevant_field': False,
            'analysis': ''
        }
        
        if not candidate_education:
            score_data['analysis'] = "No education information found"
            return score_data
        
        # Determine highest degree
        degree_hierarchy = {
            'phd': 100,
            'doctorate': 100,
            'doctoral': 100,
            'master': 80,
            'm.s': 80,
            'm.a': 80,
            'mba': 80,
            'bachelor': 60,
            'b.s': 60,
            'b.a': 60,
            'associate': 40,
            'a.s': 40,
        }
        
        highest_score = 0
        highest_degree = ''
        
        for edu in candidate_education:
            degree = edu.get('degree', '').lower()
            for key, value in degree_hierarchy.items():
                if key in degree:
                    if value > highest_score:
                        highest_score = value
                        highest_degree = edu.get('degree', '')
        
        score_data['highest_degree'] = highest_degree
        score_data['score'] = highest_score if highest_score > 0 else 50.0
        
        # Check for relevant field
        tech_fields = ['computer', 'software', 'engineering', 'technology', 'science', 'mathematics']
        for edu in candidate_education:
            degree_text = edu.get('degree', '').lower()
            field_text = edu.get('field', '').lower()
            
            if any(field in degree_text or field in field_text for field in tech_fields):
                score_data['relevant_field'] = True
                score_data['score'] = min(score_data['score'] + 10, 100.0)
                break
        
        score_data['analysis'] = f"Highest degree: {highest_degree or 'Not specified'}"
        if score_data['relevant_field']:
            score_data['analysis'] += " (relevant field)"
        
        return score_data
    
    async def generate_llm_based_score(
        self,
        job: Job,
        application: Application,
        match_scores: Dict[str, Any],
        ats_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Use LLM to generate a more nuanced score and explanation
        """
        try:
            # Prepare context
            job_skills = self._ensure_list(job.key_skills)
            candidate_skills = self._ensure_list(application.parsed_skills)
            
            # Build concise prompt for LLM evaluation
            prompt = f"""Evaluate this candidate for the {job.title} position.

JOB REQUIREMENTS:
- Title: {job.title}
- Required Skills: {', '.join(job_skills[:10])}
- Experience: {getattr(job, 'required_experience', 'Not specified')}

CANDIDATE PROFILE:
- Skills: {', '.join(candidate_skills[:15])}
- Experience: {len(self._ensure_list(application.parsed_experience))} roles
- Education: {len(self._ensure_list(application.parsed_education))} degrees

PRELIMINARY SCORES:
- Skills Match: {match_scores.get('skills_score', 0):.1f}%
- Experience Match: {match_scores.get('experience_score', 0):.1f}%
- Education Match: {match_scores.get('education_score', 0):.1f}%
- ATS Score: {sum(ats_scores.values()):.1f}%

Provide a JSON response with:
{{
  "overall_score": <0-100>,
  "confidence": <"high"|"medium"|"low">,
  "key_strengths": ["strength1", "strength2", "strength3"],
  "key_gaps": ["gap1", "gap2", "gap3"],
  "recommendation": "<hire|interview|reject>",
  "brief_summary": "<2-3 sentences>"
}}"""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert technical recruiter. Evaluate candidates objectively based on job requirements. Respond with valid JSON only."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            logger.info(f"Requesting LLM-based evaluation for application {application.id}")
            
            response = await self.llm_service._chat_ollama(
                messages,
                temperature=0.2,
                max_tokens=500,
                timeout=60
            )
            
            # Parse JSON response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start != -1 and json_end > json_start:
                json_text = response[json_start:json_end]
                llm_evaluation = json.loads(json_text)
                
                logger.info(f"LLM evaluation completed for application {application.id}")
                return llm_evaluation
            else:
                logger.warning("No valid JSON in LLM response, using fallback")
                return self._fallback_llm_evaluation(match_scores, ats_scores)
                
        except Exception as e:
            logger.error(f"Error in LLM-based scoring: {e}")
            return self._fallback_llm_evaluation(match_scores, ats_scores)
    
    def _fallback_llm_evaluation(
        self,
        match_scores: Dict[str, Any],
        ats_scores: Dict[str, float]
    ) -> Dict[str, Any]:
        """Fallback evaluation when LLM fails"""
        avg_match = (
            match_scores.get('skills_score', 0) +
            match_scores.get('experience_score', 0) +
            match_scores.get('education_score', 0)
        ) / 3
        
        avg_ats = sum(ats_scores.values()) / len(ats_scores) if ats_scores else 0
        overall = (avg_match + avg_ats) / 2
        
        return {
            "overall_score": round(overall, 1),
            "confidence": "medium",
            "key_strengths": ["Meets basic requirements"],
            "key_gaps": ["Requires detailed review"],
            "recommendation": "interview" if overall >= 60 else "reject",
            "brief_summary": f"Candidate scored {overall:.1f}% overall. Automated evaluation suggests {'further review' if overall >= 60 else 'not a strong match'}."
        }
    
    async def score_application_enhanced(
        self,
        db: Session,
        application: Application,
        use_llm_evaluation: bool = True
    ) -> ApplicationScore:
        """
        Enhanced scoring with better matching and LLM evaluation
        """
        try:
            # Get job details
            job = db.query(Job).filter(Job.id == application.job_id).first()
            if not job:
                raise ValueError(f"Job not found for application {application.id}")
            
            logger.info(f"Starting enhanced scoring for application {application.id}")
            
            # Get parsed data
            job_skills = self._ensure_list(job.key_skills)
            candidate_skills = self._ensure_list(application.parsed_skills)
            candidate_experience = self._ensure_list(application.parsed_experience)
            candidate_education = self._ensure_list(application.parsed_education)
            
            # 1. Calculate semantic skill match
            skills_score, matched_skills, missing_skills, extra_skills = \
                self.calculate_semantic_skill_match(job_skills, candidate_skills)
            
            # 2. Calculate experience match
            experience_data = self.calculate_experience_match(job, candidate_experience)
            
            # 3. Calculate education match
            education_data = self.calculate_education_match(job, candidate_education)
            
            # 4. Get ATS scores (from enhanced parser if available)
            if hasattr(application, 'ats_score_breakdown') and application.ats_score_breakdown:
                ats_scores = application.ats_score_breakdown
            else:
                # Fallback to basic ATS scoring
                ats_scores = {
                    'format_score': 25.0 if application.resume_filename.lower().endswith(('.pdf', '.docx')) else 10.0,
                    'structure_score': 20.0 if candidate_skills else 10.0,
                    'keyword_score': min(len(candidate_skills) * 2, 25.0),
                    'readability_score': 20.0
                }
            
            # Prepare match scores
            match_scores = {
                'skills_score': skills_score,
                'skills_matched': matched_skills,
                'skills_missing': missing_skills,
                'skills_extra': extra_skills,
                'experience_score': experience_data['score'],
                'experience_analysis': experience_data['analysis'],
                'education_score': education_data['score'],
                'education_analysis': education_data['analysis']
            }
            
            # 5. Calculate weighted scores
            avg_match_score = (
                skills_score * 0.5 +
                experience_data['score'] * 0.3 +
                education_data['score'] * 0.2
            )
            
            avg_ats_score = sum(ats_scores.values())
            
            # 6. Get LLM evaluation if enabled
            llm_evaluation = None
            if use_llm_evaluation:
                llm_evaluation = await self.generate_llm_based_score(
                    job, application, match_scores, ats_scores
                )
                
                # Use LLM score if available and reasonable
                if llm_evaluation and 'overall_score' in llm_evaluation:
                    final_score = llm_evaluation['overall_score']
                else:
                    final_score = (avg_match_score * self.match_weight) + (avg_ats_score * self.ats_weight)
            else:
                final_score = (avg_match_score * self.match_weight) + (avg_ats_score * self.ats_weight)
            
            # 7. Generate detailed feedback
            feedback = self._generate_detailed_feedback(
                match_scores, ats_scores, llm_evaluation
            )
            
            # 8. Create score record
            application_score = ApplicationScore(
                application_id=application.id,
                match_score=avg_match_score,
                ats_score=avg_ats_score,
                final_score=round(final_score, 2),
                skills_match=skills_score,
                experience_match=experience_data['score'],
                education_match=education_data['score'],
                certification_match=0.0,  # Can be enhanced
                ats_format_score=ats_scores.get('format_score', 0),
                ats_keywords_score=ats_scores.get('keyword_score', 0),
                ats_structure_score=ats_scores.get('structure_score', 0),
                scoring_details={
                    'match_scores': match_scores,
                    'ats_scores': ats_scores,
                    'llm_evaluation': llm_evaluation
                },
                ai_feedback=feedback,
                score_explanation=llm_evaluation.get('brief_summary', '') if llm_evaluation else feedback
            )
            
            db.add(application_score)
            db.commit()
            db.refresh(application_score)
            
            logger.info(f"Enhanced scoring completed for application {application.id}. Final score: {final_score:.2f}")
            
            # Update application status
            self._update_application_status(db, application, final_score, llm_evaluation)
            
            return application_score
            
        except Exception as e:
            logger.error(f"Error in enhanced scoring for application {application.id}: {e}", exc_info=True)
            db.rollback()
            raise
    
    def _generate_detailed_feedback(
        self,
        match_scores: Dict[str, Any],
        ats_scores: Dict[str, float],
        llm_evaluation: Dict[str, Any] = None
    ) -> str:
        """Generate detailed human-readable feedback"""
        feedback_parts = []
        
        # Skills feedback
        skills_score = match_scores.get('skills_score', 0)
        matched = match_scores.get('skills_matched', [])
        missing = match_scores.get('skills_missing', [])
        
        if skills_score >= 80:
            feedback_parts.append(f"Excellent skill match ({skills_score:.0f}%). Candidate has {len(matched)} required skills.")
        elif skills_score >= 60:
            feedback_parts.append(f"Good skill match ({skills_score:.0f}%). Missing {len(missing)} key skills.")
        else:
            feedback_parts.append(f"Limited skill match ({skills_score:.0f}%). Significant skill gaps identified.")
        
        # Experience feedback
        exp_score = match_scores.get('experience_score', 0)
        exp_analysis = match_scores.get('experience_analysis', '')
        feedback_parts.append(f"Experience: {exp_analysis}")
        
        # Education feedback
        edu_analysis = match_scores.get('education_analysis', '')
        feedback_parts.append(f"Education: {edu_analysis}")
        
        # ATS feedback
        ats_total = sum(ats_scores.values())
        if ats_total >= 80:
            feedback_parts.append("Resume is well-optimized for ATS systems.")
        elif ats_total >= 60:
            feedback_parts.append("Resume has good ATS compatibility with room for improvement.")
        else:
            feedback_parts.append("Resume needs optimization for ATS systems.")
        
        # LLM insights
        if llm_evaluation:
            if 'key_strengths' in llm_evaluation and llm_evaluation['key_strengths']:
                strengths = ', '.join(llm_evaluation['key_strengths'][:2])
                feedback_parts.append(f"Key strengths: {strengths}.")
            
            if 'recommendation' in llm_evaluation:
                rec = llm_evaluation['recommendation']
                feedback_parts.append(f"Recommendation: {rec.capitalize()}.")
        
        return " ".join(feedback_parts)
    
    def _update_application_status(
        self,
        db: Session,
        application: Application,
        final_score: float,
        llm_evaluation: Dict[str, Any] = None
    ):
        """Update application status based on score and LLM recommendation"""
        # Use LLM recommendation if available
        if llm_evaluation and 'recommendation' in llm_evaluation:
            rec = llm_evaluation['recommendation'].lower()
            if rec == 'hire' or final_score >= self.shortlist_threshold:
                application.status = 'selected'
            elif rec == 'interview' or final_score >= self.requalify_threshold:
                application.status = 'under_review'
            else:
                application.status = 'rejected'
        else:
            # Fallback to score-based decision
            if final_score >= self.shortlist_threshold:
                application.status = 'selected'
            elif final_score >= self.requalify_threshold:
                application.status = 'under_review'
            else:
                application.status = 'rejected'
        
        db.commit()
    
    @staticmethod
    def _ensure_list(data):
        """Helper to ensure data is a list"""
        if isinstance(data, str):
            try:
                return json.loads(data)
            except:
                return []
        return data if data is not None else []
