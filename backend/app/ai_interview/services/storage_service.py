"""Storage service for MinIO/S3"""
import os
from typing import Optional
from datetime import timedelta
from minio import Minio
from minio.error import S3Error
import logging
import urllib3

# Suppress urllib3 connection warnings when MinIO is not available
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Optional: boto3 for AWS S3 (not needed for MinIO)
try:
    from botocore.exceptions import ClientError
except ImportError:
    # Define a dummy exception if boto3 is not installed
    class ClientError(Exception):
        pass
from ...config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing file storage in MinIO/S3"""
    
    def __init__(self):
        """Initialize MinIO client"""
        self.endpoint = settings.minio_endpoint or ""
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.bucket_name = settings.s3_bucket
        self.use_ssl = settings.s3_use_ssl
        self.client = None
        
        # Only initialize if endpoint is configured (not empty)
        if not self.endpoint or self.endpoint.strip() == "":
            logger.info("MinIO endpoint not configured. Storage features will be disabled.")
            logger.info("To enable storage, set MINIO_ENDPOINT in your .env file (e.g., localhost:9000)")
            return
        
        try:
            logger.info(f"Attempting to connect to MinIO at {self.endpoint}...")
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.use_ssl
            )
            
            # Test connection by checking if bucket exists (with timeout handling)
            # Use a quick connection test instead of bucket_exists which can hang
            try:
                import socket
                import urllib.parse
                
                # Parse endpoint to get host and port
                if '://' in self.endpoint:
                    parsed = urllib.parse.urlparse(f"http://{self.endpoint}")
                    host = parsed.hostname or self.endpoint.split(':')[0]
                    port = parsed.port or (9000 if not self.use_ssl else 443)
                else:
                    parts = self.endpoint.split(':')
                    host = parts[0]
                    port = int(parts[1]) if len(parts) > 1 else (9000 if not self.use_ssl else 443)
                
                # Quick socket connection test (timeout 2 seconds)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                try:
                    result = sock.connect_ex((host, port))
                    sock.close()
                    if result != 0:
                        raise ConnectionError(f"Cannot connect to {host}:{port}")
                except socket.timeout:
                    sock.close()
                    raise ConnectionError(f"Connection timeout to {host}:{port}")
                except Exception as sock_err:
                    sock.close()
                    raise ConnectionError(f"Connection failed: {sock_err}")
                
                # If socket test passed, try bucket operation
                bucket_exists = self.client.bucket_exists(self.bucket_name)
                if not bucket_exists:
                    logger.info(f"Bucket '{self.bucket_name}' does not exist, creating...")
                    self.client.make_bucket(self.bucket_name)
                    logger.info(f"Created bucket: {self.bucket_name}")
                else:
                    logger.info(f"Bucket '{self.bucket_name}' exists")
                
                logger.info(f"✅ MinIO client initialized successfully: {self.endpoint}")
            except (ConnectionError, OSError) as conn_error:
                logger.warning(f"⚠️  Cannot connect to MinIO server at {self.endpoint}")
                logger.warning(f"   Error: {conn_error}")
                logger.warning("   MinIO server is not running or endpoint is incorrect.")
                logger.warning("   The app will continue without file storage.")
                logger.warning("   To start MinIO:")
                logger.warning("   1. Run: start-minio.bat")
                logger.warning("   2. Or: docker run -d -p 9000:9000 -p 9001:9001 --name minio -e 'MINIO_ROOT_USER=minioadmin' -e 'MINIO_ROOT_PASSWORD=minioadmin' minio/minio server /data --console-address ':9001'")
                self.client = None
            except Exception as bucket_error:
                logger.warning(f"Failed to access bucket '{self.bucket_name}': {bucket_error}")
                logger.warning("MinIO connection may be unstable. Storage features may not work.")
                # Keep client but it might fail on operations
                
        except Exception as e:
            error_msg = str(e)
            if "refused" in error_msg.lower() or "10061" in error_msg or "10060" in error_msg:
                logger.warning(f"⚠️  MinIO server is not running at {self.endpoint}")
                logger.warning("   Connection refused - MinIO is not started or endpoint is wrong.")
            else:
                logger.warning(f"⚠️  MinIO connection failed: {e}")
            logger.warning("   The app will continue without file storage. Start MinIO to enable storage features.")
            logger.warning("   To start MinIO:")
            logger.warning("   1. Run: start-minio.bat")
            logger.warning("   2. Or: docker run -d -p 9000:9000 -p 9001:9001 --name minio -e 'MINIO_ROOT_USER=minioadmin' -e 'MINIO_ROOT_PASSWORD=minioadmin' minio/minio server /data --console-address ':9001'")
            self.client = None
    
    def upload_file(
        self,
        file_path: str,
        object_name: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Upload file to storage
        
        Args:
            file_path: Local file path
            object_name: Object name in bucket
            content_type: Optional content type
            
        Returns:
            Object URL
        """
        if not self.client:
            raise RuntimeError(f"Storage client not initialized. MinIO endpoint: {self.endpoint or 'NOT SET'}")
        
        try:
            self.client.fput_object(
                self.bucket_name,
                object_name,
                file_path,
                content_type=content_type
            )
            return f"{self.bucket_name}/{object_name}"
        except S3Error as e:
            logger.error(f"Failed to upload file: {e}")
            raise
    
    def download_file(self, object_name: str, file_path: str) -> None:
        """
        Download file from storage
        
        Args:
            object_name: Object name in bucket
            file_path: Local file path to save
        """
        if not self.client:
            raise RuntimeError(f"Storage client not initialized. MinIO endpoint: {self.endpoint or 'NOT SET'}")
        
        try:
            self.client.fget_object(self.bucket_name, object_name, file_path)
        except S3Error as e:
            logger.error(f"Failed to download file: {e}")
            raise
    
    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """
        Get presigned URL for object access
        
        Args:
            object_name: Object name in bucket
            expires: Expiration time
            
        Returns:
            Presigned URL
        """
        if not self.client:
            raise RuntimeError(f"Storage client not initialized. MinIO endpoint: {self.endpoint or 'NOT SET'}")
        
        try:
            return self.client.presigned_get_object(
                self.bucket_name,
                object_name,
                expires=expires
            )
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def delete_file(self, object_name: str) -> None:
        """
        Delete file from storage
        
        Args:
            object_name: Object name in bucket
        """
        if not self.client:
            raise RuntimeError("Storage client not initialized")
        
        try:
            self.client.remove_object(self.bucket_name, object_name)
        except S3Error as e:
            logger.error(f"Failed to delete file: {e}")
            raise
    
    def get_session_path(self, session_id: int, path_type: str) -> str:
        """
        Get storage path for session artifacts
        
        Args:
            session_id: Session ID
            path_type: 'raw', 'clips', or 'artifacts'
            
        Returns:
            Storage path
        """
        return f"sessions/{session_id}/{path_type}/"
    
    def get_clip_path(self, session_id: int, flag_id: int) -> str:
        """Get storage path for a flag clip"""
        return f"sessions/{session_id}/clips/flag_{flag_id}.mp4"
    
    def get_transcript_path(self, session_id: int) -> str:
        """Get storage path for transcript"""
        return f"sessions/{session_id}/artifacts/transcript.json"
    
    def is_available(self) -> bool:
        """Check if storage is available and connected"""
        return self.client is not None
    
    def test_connection(self) -> bool:
        """Test if storage connection is working"""
        if not self.client:
            return False
        try:
            # Try to list buckets or check bucket existence
            self.client.bucket_exists(self.bucket_name)
            return True
        except Exception:
            return False

