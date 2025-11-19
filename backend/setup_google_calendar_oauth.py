#!/usr/bin/env python3
"""
Google Calendar OAuth Setup Script

This script helps you set up OAuth 2.0 authentication for Google Calendar API.
It will create a token.json file that allows the application to create calendar events
and Google Meet links automatically.

Prerequisites:
1. Go to Google Cloud Console (https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API
4. Create OAuth 2.0 credentials (Desktop application)
5. Download the credentials.json file to this directory

Usage:
    python setup_google_calendar_oauth.py
"""

import os
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError as e:
    print(f"❌ Missing required packages: {e}")
    print("Please install: pip install google-auth google-auth-oauthlib google-api-python-client")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    print("🚀 Google Calendar OAuth Setup")
    print("=" * 40)
    
    # Check if credentials.json exists
    if not os.path.exists('credentials.json'):
        print("❌ credentials.json not found!")
        print("\n📋 Setup Instructions:")
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create/select a project")
        print("3. Enable Google Calendar API")
        print("4. Go to Credentials > Create Credentials > OAuth 2.0 Client IDs")
        print("5. Choose 'Desktop application'")
        print("6. Download the JSON file and rename it to 'credentials.json'")
        print("7. Place credentials.json in this directory")
        print("8. Run this script again")
        return
    
    print("✅ Found credentials.json")
    
    # Check if token already exists
    if os.path.exists('token.json'):
        print("✅ Found existing token.json")
        
        # Try to load and validate existing token
        try:
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            if creds and creds.valid:
                print("✅ Existing token is valid")
                test_calendar_access(creds)
                return
            elif creds and creds.expired and creds.refresh_token:
                print("🔄 Refreshing expired token...")
                creds.refresh(Request())
                save_token(creds)
                print("✅ Token refreshed successfully")
                test_calendar_access(creds)
                return
        except Exception as e:
            print(f"⚠️ Existing token invalid: {e}")
            print("Creating new token...")
    
    # Run OAuth flow
    print("🔐 Starting OAuth flow...")
    print("📱 Your browser will open for authentication")
    
    try:
        flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        
        # Save the credentials
        save_token(creds)
        print("✅ OAuth setup completed successfully!")
        
        # Test the credentials
        test_calendar_access(creds)
        
    except Exception as e:
        print(f"❌ OAuth setup failed: {e}")
        return

def save_token(creds):
    """Save credentials to token.json"""
    with open('token.json', 'w') as token:
        token.write(creds.to_json())
    print("💾 Token saved to token.json")

def test_calendar_access(creds):
    """Test calendar access by listing calendars"""
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        print("\n🧪 Testing Calendar API access...")
        
        # List calendars
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        if not calendars:
            print("⚠️ No calendars found")
        else:
            print(f"✅ Found {len(calendars)} calendar(s):")
            for calendar in calendars[:3]:  # Show first 3
                print(f"   - {calendar['summary']} ({calendar['id']})")
        
        print("\n🎉 Google Calendar API is ready!")
        print("✅ You can now use Google Meet integration in the hiring system")
        
    except Exception as e:
        print(f"❌ Calendar API test failed: {e}")

if __name__ == "__main__":
    main()