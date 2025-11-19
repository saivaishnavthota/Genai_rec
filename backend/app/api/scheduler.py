from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.user import User
from ..api.auth import get_current_user
from ..services.scheduler_service import trigger_scheduled_tasks

router = APIRouter(prefix="/scheduler", tags=["Scheduler"])

@router.post("/trigger")
async def manual_trigger_scheduler(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger scheduled tasks (for testing and admin use)"""
    
    # Only allow admin users to trigger scheduler
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin users can trigger scheduler tasks"
        )
    
    try:
        result = await trigger_scheduled_tasks()
        return {
            "message": "Scheduled tasks triggered successfully",
            "result": result
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering scheduled tasks: {str(e)}"
        )
