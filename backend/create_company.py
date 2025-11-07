#!/usr/bin/env python3
"""
Script to create a company and add it to the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Fix Windows encoding issues
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from app.database import SessionLocal
from app.models.company import Company

def create_company(
    name: str,
    description: str = None,
    website: str = None,
    industry: str = None,
    company_size: str = None,
    location: str = None,
    theme_color: str = "#2563eb",
    logo_url: str = None
):
    """Create a company and add it to the database"""
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if company name already exists
        existing_company = db.query(Company).filter(
            Company.name == name
        ).first()
        
        if existing_company:
            print(f"[ERROR] Company with name '{name}' already exists (ID: {existing_company.id})")
            return None
        
        # Create new company
        company = Company(
            name=name,
            description=description,
            website=website,
            industry=industry,
            company_size=company_size,
            location=location,
            theme_color=theme_color,
            logo_url=logo_url,
            is_active=True
        )
        
        db.add(company)
        db.commit()
        db.refresh(company)
        
        print("[SUCCESS] Company created successfully!")
        print(f"\nCompany Details:")
        print(f"   ID: {company.id}")
        print(f"   Name: {company.name}")
        if company.description:
            print(f"   Description: {company.description}")
        if company.website:
            print(f"   Website: {company.website}")
        if company.industry:
            print(f"   Industry: {company.industry}")
        if company.company_size:
            print(f"   Company Size: {company.company_size}")
        if company.location:
            print(f"   Location: {company.location}")
        print(f"   Theme Color: {company.theme_color}")
        print(f"   Active: {company.is_active}")
        print(f"   Created At: {company.created_at}")
        
        return company
        
    except Exception as e:
        print(f"[ERROR] Error creating company: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Create a company and add it to the database")
    parser.add_argument("--name", "-n", required=True, help="Company name (required)")
    parser.add_argument("--description", "-d", help="Company description")
    parser.add_argument("--website", "-w", help="Company website URL")
    parser.add_argument("--industry", "-i", help="Company industry")
    parser.add_argument("--company-size", "-s", help="Company size (e.g., '1-10', '10-50', '50-200', '200-1000', '1000+')")
    parser.add_argument("--location", "-l", help="Company location")
    parser.add_argument("--theme-color", "-t", default="#2563eb", help="Theme color (default: #2563eb)")
    parser.add_argument("--logo-url", help="Logo URL")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        # Interactive mode
        company_name = input("Enter company name: ").strip()
        
        if not company_name:
            print("[ERROR] Company name is required!")
            sys.exit(1)
        
        # Optional fields
        description = input("Enter description (optional): ").strip() or None
        website = input("Enter website URL (optional): ").strip() or None
        industry = input("Enter industry (optional): ").strip() or None
        company_size = input("Enter company size (optional, e.g., '1-10', '10-50', '50-200', '200-1000', '1000+'): ").strip() or None
        location = input("Enter location (optional): ").strip() or None
        theme_color = input("Enter theme color (optional, default: #2563eb): ").strip() or "#2563eb"
        logo_url = input("Enter logo URL (optional): ").strip() or None
        
        create_company(
            name=company_name,
            description=description,
            website=website,
            industry=industry,
            company_size=company_size,
            location=location,
            theme_color=theme_color,
            logo_url=logo_url
        )
    else:
        # Command-line mode
        create_company(
            name=args.name,
            description=args.description,
            website=args.website,
            industry=args.industry,
            company_size=args.company_size,
            location=args.location,
            theme_color=args.theme_color,
            logo_url=args.logo_url
        )

