#!/usr/bin/env python3
"""
Setup script for Google Meet OAuth credentials.
Run this script manually to authorize the application and generate token.json
"""
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.apps import meet_v2

# Scope that allows creating Meet spaces
SCOPES = ["https://www.googleapis.com/auth/meetings.space.created"]

CREDENTIALS_FILE = "credentials.json"  # Downloaded from Google Cloud Console
TOKEN_FILE = "token.json"              # Will be created after authorization

def setup_oauth_credentials():
    """Set up OAuth credentials for Google Meet API"""
    print("🔧 GOOGLE MEET OAUTH SETUP")
    print("=" * 50)
    
    # Check if credentials.json exists
    if not os.path.exists(CREDENTIALS_FILE):
        print(f"❌ Missing {CREDENTIALS_FILE}")
        print("\n📋 SETUP INSTRUCTIONS:")
        print("1. Go to Google Cloud Console → APIs & Services")
        print("2. Create or select a project")
        print("3. Enable 'Google Meet API'")
        print("4. Create OAuth 2.0 credentials → Desktop Application")
        print("5. Download the JSON file and save as 'credentials.json'")
        print("6. Run this script again")
        return False
    
    print(f"✅ Found {CREDENTIALS_FILE}")
    
    # Load existing token if available
    creds = None
    if os.path.exists(TOKEN_FILE):
        print(f"✅ Found existing {TOKEN_FILE}")
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # Check if we need to authorize
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired credentials...")
            creds.refresh(Request())
        else:
            print("🌐 Starting OAuth authorization flow...")
            print("This will open your browser for Google authorization")
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Run local server to handle OAuth callback
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for next run
        print(f"💾 Saving credentials to {TOKEN_FILE}")
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    # Test the credentials by creating a Meet client
    try:
        client = meet_v2.SpacesServiceClient(credentials=creds)
        print("✅ Google Meet API client created successfully")
        
        # Test creating a space (optional)
        print("\n🧪 Testing Meet space creation...")
        req = meet_v2.CreateSpaceRequest()
        space = client.create_space(request=req)
        
        print("✅ TEST MEETING CREATED:")
        print(f"   Resource name: {space.name}")
        print(f"   Meeting code: {space.meeting_code}")
        print(f"   Join URL: {space.meeting_uri}")
        
        print("\n🎉 SETUP COMPLETE!")
        print("Google Meet API is now ready for automatic meeting creation")
        return True
        
    except Exception as e:
        print(f"❌ Error testing Google Meet API: {e}")
        return False

if __name__ == "__main__":
    success = setup_oauth_credentials()
    
    if success:
        print("\n📋 NEXT STEPS:")
        print("1. The backend will now automatically create real Google Meet spaces")
        print("2. Interview emails will contain actual working meeting links")
        print("3. No more manual meeting creation required!")
    else:
        print("\n⚠️  SETUP INCOMPLETE")
        print("Follow the instructions above to complete the setup")
