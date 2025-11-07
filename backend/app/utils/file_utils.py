import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException
from ..config import settings

def generate_filename(original_filename: str) -> str:
    """Generate a unique filename"""
    file_extension = Path(original_filename).suffix
    unique_id = str(uuid.uuid4())
    return f"{unique_id}{file_extension}"

async def save_uploaded_file(file: UploadFile, upload_dir: str = None) -> tuple[str, str]:
    """Save uploaded file and return filename and filepath"""
    if not upload_dir:
        upload_dir = settings.upload_dir
    
    # Create upload directory if it doesn't exist
    Path(upload_dir).mkdir(parents=True, exist_ok=True)
    
    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.max_file_size} bytes"
        )
    
    # Generate unique filename
    filename = generate_filename(file.filename)
    filepath = os.path.join(upload_dir, filename)
    
    # Save file
    with open(filepath, "wb") as buffer:
        buffer.write(content)
    
    return filename, filepath

def validate_file_type(file: UploadFile, allowed_types: list = None) -> bool:
    """Validate file type"""
    if not allowed_types:
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
            "application/msword",  # .doc
            "application/vnd.ms-word"  # alternative .doc MIME type
        ]
    
    # Also check file extension as backup (some browsers may not set correct MIME type)
    if file.content_type in allowed_types:
        return True
    
    # Check file extension as fallback
    if hasattr(file, 'filename') and file.filename:
        filename_lower = file.filename.lower()
        if filename_lower.endswith(('.pdf', '.doc', '.docx')):
            return True
    
    return False

def get_file_size(filepath: str) -> int:
    """Get file size in bytes"""
    return os.path.getsize(filepath)

def delete_file(filepath: str) -> bool:
    """Delete a file"""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False
    except Exception:
        return False
