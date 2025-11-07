"""Security utilities for AI Interview module"""
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from ...config import settings


def generate_webrtc_token(session_id: int, candidate_id: Optional[int] = None) -> str:
    """
    Generate WebRTC token for session access
    
    Args:
        session_id: AI interview session ID
        candidate_id: Optional candidate/application ID for validation
        
    Returns:
        JWT token string
    """
    payload: Dict = {
        "session_id": session_id,
        "type": "webrtc",
        "exp": datetime.utcnow() + timedelta(hours=2)  # 2 hour expiry
    }
    
    if candidate_id:
        payload["candidate_id"] = candidate_id
    
    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )


def verify_webrtc_token(token: str) -> Dict:
    """
    Verify WebRTC token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload
        
    Raises:
        jwt.InvalidTokenError: If token is invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        
        if payload.get("type") != "webrtc":
            raise jwt.InvalidTokenError("Invalid token type")
        
        return payload
    except jwt.ExpiredSignatureError:
        raise jwt.InvalidTokenError("Token expired")
    except jwt.InvalidTokenError:
        raise jwt.InvalidTokenError("Invalid token")


def generate_session_secret() -> str:
    """Generate a random secret for session"""
    return secrets.token_urlsafe(32)

