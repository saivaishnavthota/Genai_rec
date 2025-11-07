"""WebRTC service for streaming negotiation"""
import logging
from typing import Optional, Dict
from ..utils.security import generate_webrtc_token, verify_webrtc_token

logger = logging.getLogger(__name__)


class WebRTCService:
    """Service for WebRTC token negotiation"""
    
    def generate_token(
        self,
        session_id: int,
        candidate_id: Optional[int] = None
    ) -> str:
        """
        Generate WebRTC token for session
        
        Args:
            session_id: Session ID
            candidate_id: Optional candidate ID for validation
            
        Returns:
            JWT token string
        """
        return generate_webrtc_token(session_id, candidate_id)
    
    def verify_token(self, token: str) -> Dict:
        """
        Verify WebRTC token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded payload
        """
        return verify_webrtc_token(token)
    
    def get_ice_servers(self) -> list:
        """
        Get ICE servers for WebRTC (stub)
        
        Returns:
            List of ICE server configurations
        """
        # In production, would return actual STUN/TURN servers
        return [
            {"urls": "stun:stun.l.google.com:19302"}
        ]

