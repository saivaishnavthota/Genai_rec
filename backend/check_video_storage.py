#!/usr/bin/env python3
"""
Utility script to check if video files exist in storage for AI interview sessions
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config import settings
from app.ai_interview.services.storage_service import StorageService
from app.database import SessionLocal
from app.ai_interview.models.ai_sessions import AISession, AISessionFlag

def check_session_storage(session_id: int):
    """Check storage for a specific session"""
    storage = StorageService()
    
    print(f"\n{'='*60}")
    print(f"Checking storage for Session ID: {session_id}")
    print(f"{'='*60}")
    
    # Check if MinIO is configured
    if not storage.client:
        print("\n⚠️  WARNING: MinIO/S3 storage is NOT configured or not available!")
        print(f"   Endpoint: {storage.endpoint or 'NOT SET'}")
        print(f"   Bucket: {storage.bucket_name}")
        print(f"   Access Key: {storage.access_key}")
        
        if not storage.endpoint or storage.endpoint.strip() == "":
            print("\n   To enable storage:")
            print("   1. Start MinIO: Run 'start-minio.bat' or use Docker")
            print("   2. Set MINIO_ENDPOINT in backend/.env file")
            print("      Example: MINIO_ENDPOINT=localhost:9000")
            print("   3. Restart the backend server")
        else:
            print(f"\n   MinIO endpoint is configured ({storage.endpoint}) but connection failed.")
            print("   Possible issues:")
            print("   - MinIO server is not running")
            print("   - Wrong endpoint address")
            print("   - Network/firewall blocking connection")
            print("\n   To start MinIO:")
            print("   - Run: start-minio.bat")
            print("   - Or: docker run -d -p 9000:9000 -p 9001:9001 --name minio -e 'MINIO_ROOT_USER=minioadmin' -e 'MINIO_ROOT_PASSWORD=minioadmin' minio/minio server /data --console-address ':9001'")
        
        # Still check database for video URLs even if storage is not available
        print("\n📊 Checking database for video URLs...")
        db = SessionLocal()
        try:
            session = db.query(AISession).filter(AISession.id == session_id).first()
            if session:
                print(f"   Session Status: {session.status}")
                print(f"   Video URL in DB: {session.video_url or 'NOT SET'}")
                print(f"   Transcript URL in DB: {session.transcript_url or 'NOT SET'}")
                
                flags = db.query(AISessionFlag).filter(AISessionFlag.session_id == session_id).all()
                print(f"   Flags in DB: {len(flags)}")
                for flag in flags[:5]:  # Show first 5
                    print(f"      - Flag #{flag.id}: {flag.flag_type} (clip_url: {flag.clip_url or 'NOT SET'})")
        finally:
            db.close()
        
        print(f"\n{'='*60}\n")
        return
    
    print(f"\n✅ Storage configured:")
    print(f"   Endpoint: {storage.endpoint}")
    print(f"   Bucket: {storage.bucket_name}")
    
    # Check video file
    video_path = f"sessions/{session_id}/raw.mp4"
    print(f"\n📹 Video File:")
    print(f"   Path: {video_path}")
    try:
        # Try to get object info
        from minio.error import S3Error
        obj = storage.client.stat_object(storage.bucket_name, video_path)
        size_mb = obj.size / (1024 * 1024)
        print(f"   ✅ EXISTS - Size: {size_mb:.2f} MB")
        print(f"   Modified: {obj.last_modified}")
    except S3Error as e:
        if e.code == 'NoSuchKey':
            print(f"   ❌ NOT FOUND")
        else:
            print(f"   ❌ ERROR: {e}")
    
    # Check transcript
    transcript_path = f"sessions/{session_id}/artifacts/transcript.json"
    print(f"\n📝 Transcript File:")
    print(f"   Path: {transcript_path}")
    try:
        obj = storage.client.stat_object(storage.bucket_name, transcript_path)
        size_kb = obj.size / 1024
        print(f"   ✅ EXISTS - Size: {size_kb:.2f} KB")
        print(f"   Modified: {obj.last_modified}")
    except S3Error as e:
        if e.code == 'NoSuchKey':
            print(f"   ❌ NOT FOUND")
        else:
            print(f"   ❌ ERROR: {e}")
    
    # Check clips
    db = SessionLocal()
    try:
        flags = db.query(AISessionFlag).filter(
            AISessionFlag.session_id == session_id
        ).all()
        
        print(f"\n🎬 Video Clips ({len(flags)} flags):")
        for flag in flags:
            clip_path = f"sessions/{session_id}/clips/flag_{flag.id}.mp4"
            print(f"   Flag #{flag.id} ({flag.flag_type}):")
            print(f"      Path: {clip_path}")
            if flag.clip_url:
                print(f"      URL in DB: {flag.clip_url}")
            try:
                obj = storage.client.stat_object(storage.bucket_name, clip_path)
                size_mb = obj.size / (1024 * 1024)
                print(f"      ✅ EXISTS - Size: {size_mb:.2f} MB")
            except S3Error as e:
                if e.code == 'NoSuchKey':
                    print(f"      ❌ NOT FOUND")
                else:
                    print(f"      ❌ ERROR: {e}")
    finally:
        db.close()
    
    print(f"\n{'='*60}\n")

def list_all_sessions():
    """List all sessions and their storage status"""
    storage = StorageService()
    
    if not storage.client:
        print("\n⚠️  MinIO/S3 storage is NOT configured or not available!")
        print(f"   Endpoint: {storage.endpoint or 'NOT SET'}")
        print(f"   Bucket: {storage.bucket_name}")
        print("\n   To enable storage:")
        print("   1. Start MinIO: Run 'start-minio.bat' or use Docker")
        print("   2. Set MINIO_ENDPOINT in backend/.env file")
        print("      Example: MINIO_ENDPOINT=localhost:9000")
        print("   3. Restart the backend server")
        print("\n   Checking database for sessions...\n")
    
    db = SessionLocal()
    try:
        sessions = db.query(AISession).order_by(AISession.id.desc()).limit(20).all()
        
        if not sessions:
            print("No sessions found in database.")
            return
        
        print(f"\n{'='*80}")
        print(f"Session Storage Status (Last 20 sessions)")
        print(f"{'='*80}")
        print(f"{'Session ID':<12} {'Status':<15} {'Video URL':<30} {'Flags':<8}")
        print(f"{'-'*80}")
        
        for session in sessions:
            video_status = "SET" if session.video_url else "NOT SET"
            if session.video_url and len(session.video_url) > 27:
                video_display = session.video_url[:27] + "..."
            else:
                video_display = session.video_url or "NOT SET"
            
            # Count flags
            flag_count = db.query(AISessionFlag).filter(
                AISessionFlag.session_id == session.id
            ).count()
            
            # If storage is available, check if files exist
            if storage.client:
                video_path = f"sessions/{session.id}/raw.mp4"
                video_exists = False
                try:
                    storage.client.stat_object(storage.bucket_name, video_path)
                    video_exists = True
                except:
                    pass
                video_status = "✅" if video_exists else "❌"
            
            print(f"{session.id:<12} {session.status:<15} {video_display:<30} {flag_count:<8}")
        
        print(f"{'-'*80}\n")
    finally:
        db.close()

if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            session_id = int(sys.argv[1])
            check_session_storage(session_id)
        else:
            list_all_sessions()
            print("\nUsage: python check_video_storage.py [session_id]")
            print("Example: python check_video_storage.py 16")
    except Exception as e:
        import traceback
        print(f"\n❌ Error running check script: {e}")
        print(f"\nTraceback:")
        traceback.print_exc()

