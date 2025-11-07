from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.company import Company
from ..models.user import User
from ..schemas.company import CompanyCreate, CompanyResponse, CompanyUpdate
from .auth import get_current_user

router = APIRouter()

@router.post("/", response_model=CompanyResponse)
async def create_company(
    company_data: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new company (Admin only)"""
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create companies"
        )
    
    # Check if company name already exists
    existing_company = db.query(Company).filter(
        Company.name == company_data.name
    ).first()
    
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company name already exists"
        )
    
    db_company = Company(**company_data.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    
    return CompanyResponse.from_orm(db_company)

@router.get("/", response_model=List[CompanyResponse])
async def get_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all companies (Admin only) or current user's company"""
    if current_user.user_type == "admin":
        companies = db.query(Company).filter(Company.is_active == True).all()
        return [CompanyResponse.from_orm(company) for company in companies]
    else:
        if current_user.company_id:
            company = db.query(Company).filter(
                Company.id == current_user.company_id,
                Company.is_active == True
            ).first()
            return [CompanyResponse.from_orm(company)] if company else []
        return []

@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check permissions
    if current_user.user_type != "admin" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return CompanyResponse.from_orm(company)

@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a company"""
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Check permissions
    if current_user.user_type != "admin" and current_user.company_id != company_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update company fields
    update_data = company_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(company, field, value)
    
    db.commit()
    db.refresh(company)
    
    return CompanyResponse.from_orm(company)

@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete/deactivate a company (Admin only)"""
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can delete companies"
        )
    
    company = db.query(Company).filter(Company.id == company_id).first()
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    # Soft delete by deactivating
    company.is_active = False
    db.commit()
    
    return {"message": "Company deactivated successfully"}
