from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.user import User
from ..schemas.user import UserResponse, UserUpdate, UserCreate
from ..utils.auth import get_password_hash
from .auth import get_current_user

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def get_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all users (Admin only) or company users (HR)"""
    if current_user.user_type == "admin":
        users = db.query(User).filter(User.is_active == True).all()
        return [UserResponse.from_orm(user) for user in users]
    elif current_user.user_type == "hr":
        users = db.query(User).filter(
            User.company_id == current_user.company_id,
            User.is_active == True
        ).all()
        return [UserResponse.from_orm(user) for user in users]
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.user_type == "admin":
        pass  # Admin can see all users
    elif current_user.user_type == "hr" and user.company_id == current_user.company_id:
        pass  # HR can see company users
    elif current_user.id == user_id:
        pass  # Users can see their own profile
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return UserResponse.from_orm(user)

@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new user (Admin and HR only)"""
    if current_user.user_type not in ["admin", "hr"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and HR can create users"
        )
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # For HR users, enforce company constraint
    if current_user.user_type == "hr":
        if user_data.company_id != current_user.company_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HR can only create users for their own company"
            )
        if user_data.user_type not in ["account_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HR can only create account manager users"
            )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        user_type=user_data.user_type,
        company_id=user_data.company_id
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.from_orm(db_user)

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.user_type == "admin":
        pass  # Admin can update all users
    elif current_user.user_type == "hr" and user.company_id == current_user.company_id:
        # HR can update company users but with restrictions
        if user_data.user_type and user_data.user_type not in ["account_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HR can only manage account manager users"
            )
    elif current_user.id == user_id:
        # Users can update their own profile (limited fields)
        restricted_fields = ["user_type", "company_id", "is_active"]
        update_dict = user_data.dict(exclude_unset=True)
        if any(field in update_dict for field in restricted_fields):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update restricted fields"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete/deactivate a user"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check permissions
    if current_user.user_type == "admin":
        pass  # Admin can delete all users
    elif current_user.user_type == "hr" and user.company_id == current_user.company_id:
        if user.user_type not in ["account_manager"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="HR can only delete account manager users"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    # Soft delete by deactivating
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}
