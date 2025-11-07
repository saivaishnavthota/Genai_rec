#!/usr/bin/env python3
"""
Database initialization script for GenAI Hiring System
Creates initial test data including companies and users
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, create_tables
from app.models.company import Company
from app.models.user import User
from app.utils.auth import get_password_hash

def init_database():
    """Initialize database with test data"""
    
    # Create all tables
    print("Creating database tables...")
    create_tables()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        if db.query(Company).first():
            print("Database already has data. Skipping initialization.")
            return
        
        print("Creating initial data...")
        
        # Create test company
        company = Company(
            name="nxzen",
            description="A leading technology company focused on innovation and growth",
            website="https://nxzenn.com",
            industry="Technology",
            company_size="100-500",
            location="San Francisco, CA",
            theme_color="#2563eb"
        )
        db.add(company)
        db.commit()
        db.refresh(company)
        
        # Create test users
        users_data = [
            {
                "email": "admin@example.com",
                "full_name": "System Administrator",
                "user_type": "admin",
                "company_id": None
            },
            {
                "email": "hr@example.com", 
                "full_name": "HR Manager",
                "user_type": "hr",
                "company_id": company.id
            },
            {
                "email": "manager@example.com",
                "full_name": "Account Manager",
                "user_type": "account_manager", 
                "company_id": company.id
            }
        ]
        
        default_password = "password123"
        hashed_password = get_password_hash(default_password)
        
        for user_data in users_data:
            user = User(
                email=user_data["email"],
                full_name=user_data["full_name"],
                hashed_password=hashed_password,
                user_type=user_data["user_type"],
                company_id=user_data["company_id"],
                is_active=True
            )
            db.add(user)
        
        db.commit()
        
        print("✅ Database initialized successfully!")
        print("\n👥 Test Users Created:")
        print(f"   Admin: admin@example.com (password: {default_password})")
        print(f"   HR: hr@example.com (password: {default_password})")
        print(f"   Account Manager: manager@example.com (password: {default_password})")
        print(f"\n🏢 Test Company: {company.name} (ID: {company.id})")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
