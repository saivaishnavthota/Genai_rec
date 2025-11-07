#!/usr/bin/env python3
"""
Script to verify companies in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.company import Company

def list_companies():
    """List all companies in the database"""
    
    db = SessionLocal()
    
    try:
        companies = db.query(Company).all()
        
        if not companies:
            print("No companies found in the database.")
            return
        
        print(f"\nFound {len(companies)} company(ies) in the database:\n")
        
        for company in companies:
            print(f"ID: {company.id}")
            print(f"Name: {company.name}")
            if company.description:
                print(f"Description: {company.description}")
            if company.website:
                print(f"Website: {company.website}")
            if company.industry:
                print(f"Industry: {company.industry}")
            if company.company_size:
                print(f"Company Size: {company.company_size}")
            if company.location:
                print(f"Location: {company.location}")
            print(f"Theme Color: {company.theme_color}")
            print(f"Active: {company.is_active}")
            print(f"Created At: {company.created_at}")
            print("-" * 50)
        
    except Exception as e:
        print(f"Error listing companies: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    list_companies()

