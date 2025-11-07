"""
Google Meet integration service using Google Meet REST API v2 with OAuth for creating real meeting spaces.
"""
import os
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleMeetService:
    """Service for creating Google Meet spaces using the Meet REST API v2 with OAuth"""
    
    # Scope that allows creating Meet spaces
    SCOPES = ["https://www.googleapis.com/auth/meetings.space.created"]
    
    def __init__(self):
        self.credentials = None
        self.meet_client = None
        self.credentials_file = "credentials.json"
        self.token_file = "token.json"
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Meet service with OAuth credentials"""
        try:
            # Check for OAuth credentials files
            credentials_path = os.path.join(os.path.dirname(__file__), '..', '..', self.credentials_file)
            token_path = os.path.join(os.path.dirname(__file__), '..', '..', self.token_file)
            
            # Try to load existing token
            if os.path.exists(token_path):
                self.credentials = Credentials.from_authorized_user_file(token_path, self.SCOPES)
            
            # Refresh or get new credentials if needed
            if not self.credentials or not self.credentials.valid:
                if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                    logger.info("Refreshing Google Meet API credentials")
                    self.credentials.refresh(Request())
                else:
                    if not os.path.exists(credentials_path):
                        logger.warning(f"Google OAuth credentials file not found: {self.credentials_file}")
                        logger.info("To enable Google Meet API:")
                        logger.info("1. Download OAuth Desktop client JSON from Google Cloud Console")
                        logger.info("2. Save as credentials.json in the backend root directory")
                        return
                    
                    # For server environment, we can't run interactive OAuth flow
                    # This would require a web-based OAuth flow or pre-authorized tokens
                    logger.warning("OAuth credentials expired and no refresh token available")
                    logger.info("Google Meet API requires manual OAuth authorization")
                    return
                
                # Save refreshed credentials
                if self.credentials and self.credentials.valid:
                    with open(token_path, 'w') as f:
                        f.write(self.credentials.to_json())
            
            # Import and initialize Meet client
            try:
                from google.apps import meet_v2
                self.meet_client = meet_v2.SpacesServiceClient(credentials=self.credentials)
                logger.info("Google Meet API service initialized successfully with OAuth")
            except ImportError:
                logger.warning("google-apps-meet package not available. Install with: pip install google-apps-meet")
                self.meet_client = None
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Meet service: {e}")
            self.credentials = None
            self.meet_client = None
    
    def is_available(self) -> bool:
        """Check if Google Meet service is available"""
        return self.credentials is not None and self.meet_client is not None
    
    def _get_credentials(self):
        """Get service account credentials"""
        return self.credentials
    
    def create_interview_meeting(
        self,
        candidate_email: str,
        candidate_name: str,
        primary_interviewer_email: str,
        primary_interviewer_name: str,
        backup_interviewer_email: Optional[str],
        backup_interviewer_name: Optional[str],
        interview_date: str,
        interview_time: str,
        job_title: str,
        duration_minutes: int = 60
    ) -> Dict:
        """
        Create a Google Meet space for an interview using Meet REST API v2
        
        Args:
            candidate_email: Candidate's email
            candidate_name: Candidate's name
            primary_interviewer_email: Primary interviewer's email
            primary_interviewer_name: Primary interviewer's name
            backup_interviewer_email: Backup interviewer's email (optional)
            backup_interviewer_name: Backup interviewer's name (optional)
            interview_date: Interview date (YYYY-MM-DD)
            interview_time: Interview time (HH:MM)
            job_title: Job title for the interview
            duration_minutes: Interview duration in minutes
        
        Returns:
            Dict with success status, meet_link, meeting_code, and space_name
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Google Meet service not configured",
                "meet_link": None,
                "meeting_code": None,
                "space_name": None,
                "calendar_event_id": None
            }
        
        try:
            # Import meet_v2 here to handle potential import issues
            from google.apps import meet_v2
            
            # Create a new Meet space using the Meet API v2
            # The CreateSpaceRequest can be empty for a basic space
            request = meet_v2.CreateSpaceRequest()
            
            # Create the space
            space = self.meet_client.create_space(request=request)
            
            logger.info(f"Google Meet space created successfully")
            logger.info(f"Space name: {space.name}")
            logger.info(f"Meeting URI: {space.meeting_uri}")
            logger.info(f"Meeting code: {space.meeting_code}")
            
            return {
                "success": True,
                "meet_link": space.meeting_uri,  # This is the shareable join URL
                "meeting_code": space.meeting_code,  # Human-readable meeting code
                "space_name": space.name,  # API resource name (e.g., spaces/abc123)
                "calendar_event_id": space.name,  # Use space name as identifier
                "message": "Google Meet space created successfully"
            }
            
        except ImportError as e:
            logger.error(f"Google Meet API not available: {e}")
            return {
                "success": False,
                "error": "Google Meet API package not installed",
                "meet_link": None,
                "meeting_code": None,
                "space_name": None,
                "calendar_event_id": None
            }
        except Exception as e:
            logger.error(f"Failed to create Google Meet space: {e}")
            return {
                "success": False,
                "error": str(e),
                "meet_link": None,
                "meeting_code": None,
                "space_name": None,
                "calendar_event_id": None
            }
    
    def end_active_conference(self, space_name: str) -> Dict[str, Any]:
        """
        End an active conference in a Meet space
        
        Args:
            space_name: The space resource name (e.g., spaces/abc123)
        
        Returns:
            Dict with success status and message
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Google Meet service not configured"
            }
        
        try:
            from google.apps import meet_v2
            
            # End the active conference in the space
            request = meet_v2.EndActiveConferenceRequest(name=space_name)
            self.meet_client.end_active_conference(request=request)
            
            logger.info(f"Active conference ended for space: {space_name}")
            
            return {
                "success": True,
                "message": "Active conference ended successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to end active conference: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # Legacy methods for backward compatibility
    def update_interview_meeting(self, calendar_event_id: str, updates: Dict) -> Dict:
        """Legacy method - Google Meet spaces don't need updating like calendar events"""
        return {
            "success": True,
            "message": "Google Meet spaces are persistent and don't require updates"
        }
    
    def cancel_interview_meeting(self, calendar_event_id: str) -> Dict:
        """Legacy method - Use end_active_conference instead for Meet spaces"""
        if calendar_event_id.startswith('spaces/'):
            return self.end_active_conference(calendar_event_id)
        else:
            return {
                "success": True,
                "message": "Google Meet spaces are persistent - conference can be ended manually"
            }