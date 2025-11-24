import asyncio
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..database import get_db
from ..models.application import Application, ApplicationScore
from ..services.scoring_service import ScoringService
from ..utils.resume_parser import parse_resume

logger = logging.getLogger(__name__)

class ApplicationProcessorService:
    """Background service to process incomplete applications (missing scores or descriptions)"""
    
    def __init__(self):
        self.scoring_service = ScoringService()
        self.processing = False  # Track if currently processing
    
    async def process_incomplete_application(self, db: Session, application: Application) -> bool:
        """
        Process a single incomplete application.
        Returns True if processing was successful, False otherwise.
        """
        try:
            logger.info(f"🔄 Processing incomplete application {application.id} (candidate: {application.full_name})")
            
            # Check if application needs parsing
            needs_parsing = (
                application.parsed_skills is None or
                application.parsed_experience is None or
                application.parsed_education is None
            )
            
            if needs_parsing:
                logger.info(f"📄 Parsing resume for application {application.id}")
                try:
                    parsed_data = parse_resume(application.resume_path, application.resume_filename)
                    
                    application.parsed_skills = parsed_data.get('parsed_skills', [])
                    application.parsed_experience = parsed_data.get('parsed_experience', [])
                    application.parsed_education = parsed_data.get('parsed_education', [])
                    application.parsed_certifications = parsed_data.get('parsed_certifications', [])
                    
                    db.commit()
                    db.refresh(application)
                    logger.info(f"✅ Resume parsed for application {application.id}")
                except Exception as parse_error:
                    logger.error(f"❌ Error parsing resume for application {application.id}: {parse_error}")
                    # Continue anyway - might still be able to score with partial data
            
            # Check if application needs scoring
            latest_score = db.query(ApplicationScore).filter(
                ApplicationScore.application_id == application.id
            ).order_by(ApplicationScore.created_at.desc()).first()
            
            needs_scoring = latest_score is None
            needs_description = latest_score is not None and (
                latest_score.score_explanation is None or 
                latest_score.score_explanation.strip() == ""
            )
            
            if needs_scoring:
                logger.info(f"📊 Scoring application {application.id}")
                try:
                    score = await self.scoring_service.score_application(db, application)
                    logger.info(f"✅ Application {application.id} scored successfully. Final score: {score.final_score}")
                    return True
                except Exception as score_error:
                    logger.error(f"❌ Error scoring application {application.id}: {score_error}", exc_info=True)
                    return False
            
            elif needs_description:
                logger.info(f"📝 Generating LLM description for application {application.id}")
                try:
                    # Get job details
                    from ..models.job import Job
                    job = db.query(Job).filter(Job.id == application.job_id).first()
                    if not job:
                        logger.error(f"❌ Job not found for application {application.id}")
                        return False
                    
                    # Generate explanation
                    explanation = await self.scoring_service.generate_llm_score_explanation(
                        job=job,
                        application=application,
                        match_score=latest_score.match_score,
                        ats_score=latest_score.ats_score,
                        final_score=latest_score.final_score,
                        match_scores={
                            'skills_match': latest_score.skills_match or 0,
                            'experience_match': latest_score.experience_match or 0,
                            'education_match': latest_score.education_match or 0,
                            'certification_match': latest_score.certification_match or 0
                        },
                        ats_scores={
                            'ats_format_score': latest_score.ats_format_score or 0,
                            'ats_keywords_score': latest_score.ats_keywords_score or 0,
                            'ats_structure_score': latest_score.ats_structure_score or 0
                        }
                    )
                    
                    if explanation:
                        latest_score.score_explanation = explanation
                        db.commit()
                        logger.info(f"✅ LLM description generated for application {application.id} ({len(explanation)} chars)")
                        return True
                    else:
                        logger.warning(f"⚠️ LLM description generation returned None for application {application.id}")
                        return False
                        
                except Exception as desc_error:
                    logger.error(f"❌ Error generating description for application {application.id}: {desc_error}", exc_info=True)
                    return False
            
            else:
                logger.info(f"✅ Application {application.id} is already complete (has score and description)")
                return True
                
        except Exception as e:
            logger.error(f"❌ Unexpected error processing application {application.id}: {e}", exc_info=True)
            db.rollback()
            return False
    
    def get_incomplete_applications(self, db: Session) -> List[Application]:
        """
        Get all applications that are missing scores or descriptions.
        An application is incomplete if:
        1. It has no ApplicationScore record, OR
        2. It has an ApplicationScore but score_explanation is None or empty
        """
        try:
            # Get all applications
            all_applications = db.query(Application).all()
            incomplete = []
            
            for app in all_applications:
                # Check if has score
                latest_score = db.query(ApplicationScore).filter(
                    ApplicationScore.application_id == app.id
                ).order_by(ApplicationScore.created_at.desc()).first()
                
                if latest_score is None:
                    # No score at all
                    incomplete.append(app)
                elif latest_score.score_explanation is None or latest_score.score_explanation.strip() == "":
                    # Has score but no description
                    incomplete.append(app)
            
            return incomplete
            
        except Exception as e:
            logger.error(f"Error getting incomplete applications: {e}", exc_info=True)
            return []
    
    async def process_all_incomplete(self, db: Session) -> dict:
        """
        Process all incomplete applications.
        Returns dict with processing statistics.
        """
        if self.processing:
            logger.warning("⚠️ Application processor is already running, skipping this run")
            return {"status": "already_running", "processed": 0, "failed": 0}
        
        self.processing = True
        try:
            incomplete = self.get_incomplete_applications(db)
            
            if not incomplete:
                logger.info("✅ All applications are complete! No processing needed.")
                return {
                    "status": "all_complete",
                    "total_incomplete": 0,
                    "processed": 0,
                    "failed": 0
                }
            
            logger.info(f"🔄 Found {len(incomplete)} incomplete applications. Starting processing...")
            
            processed = 0
            failed = 0
            
            for app in incomplete:
                try:
                    success = await self.process_incomplete_application(db, app)
                    if success:
                        processed += 1
                    else:
                        failed += 1
                    
                    # Small delay between applications to avoid overwhelming the system
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing application {app.id}: {e}")
                    failed += 1
            
            logger.info(f"✅ Processing complete: {processed} processed, {failed} failed out of {len(incomplete)} incomplete")
            
            return {
                "status": "completed",
                "total_incomplete": len(incomplete),
                "processed": processed,
                "failed": failed
            }
            
        finally:
            self.processing = False
    
    async def process_application_immediately(self, application_id: int) -> bool:
        """
        Process a specific application immediately (called when application is submitted).
        This runs in the background and doesn't block.
        """
        db = None
        try:
            db = next(get_db())
            application = db.query(Application).filter(Application.id == application_id).first()
            
            if not application:
                logger.error(f"❌ Application {application_id} not found")
                return False
            
            # Process in background
            success = await self.process_incomplete_application(db, application)
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Error processing application {application_id} immediately: {e}", exc_info=True)
            if db:
                try:
                    db.rollback()
                except:
                    pass
            return False
        finally:
            if db:
                try:
                    db.close()
                except:
                    pass

# Create global service instance
application_processor_service = ApplicationProcessorService()

