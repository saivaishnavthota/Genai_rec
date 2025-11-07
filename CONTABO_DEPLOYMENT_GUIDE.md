# GenAI Hiring System - Contabo Server Deployment Guide

## 🚀 Complete Production Deployment Guide for Contabo Server

This comprehensive guide covers all necessary changes, configurations, and steps to deploy the GenAI Hiring System on a Contabo server with proper environment management using Dynaconf.

## 📋 Table of Contents

1. [Server Preparation](#server-preparation)
2. [Dynaconf Implementation](#dynaconf-implementation)
3. [Code Changes Required](#code-changes-required)
4. [Domain and SSL Configuration](#domain-and-ssl-configuration)
5. [Docker Configuration Updates](#docker-configuration-updates)
6. [Environment Configuration](#environment-configuration)
7. [Deployment Steps](#deployment-steps)
8. [Post-Deployment Configuration](#post-deployment-configuration)
9. [Monitoring and Maintenance](#monitoring-and-maintenance)
10. [Troubleshooting](#troubleshooting)

---

## 1. Server Preparation

### 1.1 Contabo Server Requirements

**Recommended Server Specifications:**
- **CPU**: 4+ cores
- **RAM**: 16GB minimum (32GB recommended)
- **Storage**: 200GB SSD
- **OS**: Ubuntu 22.04 LTS
- **Network**: Unmetered bandwidth

### 1.2 Initial Server Setup

```bash
# Connect to your Contabo server
ssh root@your-server-ip

# Update system packages
apt update && apt upgrade -y

# Install essential packages
apt install -y curl wget git vim htop ufw fail2ban

# Create application user
useradd -m -s /bin/bash genai
usermod -aG sudo genai

# Set up SSH key authentication (recommended)
mkdir -p /home/genai/.ssh
cp ~/.ssh/authorized_keys /home/genai/.ssh/
chown -R genai:genai /home/genai/.ssh
chmod 700 /home/genai/.ssh
chmod 600 /home/genai/.ssh/authorized_keys

# Configure firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker genai

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Switch to application user
su - genai
```

### 1.3 Domain Configuration

**Prerequisites:**
- Purchase a domain (e.g., `yourdomain.com`)
- Configure DNS A records:
  - `yourdomain.com` → Your Contabo server IP
  - `api.yourdomain.com` → Your Contabo server IP
  - `www.yourdomain.com` → Your Contabo server IP

---

## 2. Dynaconf Implementation

### 2.1 Backend Dynaconf Setup

**Add to `backend/requirements.txt`:**
```txt
dynaconf==3.2.4
```

**Create `backend/app/config.py` (Replace existing):**
```python
from dynaconf import Dynaconf
from pathlib import Path
import os

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Initialize Dynaconf
settings = Dynaconf(
    envvar_prefix="GENAI",
    settings_files=[
        str(BASE_DIR / "settings.toml"),
        str(BASE_DIR / "settings.local.toml"),
        str(BASE_DIR / ".secrets.toml"),
    ],
    environments=True,
    load_dotenv=True,
    dotenv_path=str(BASE_DIR.parent / ".env"),
    env_switcher="GENAI_ENV",
    merge_enabled=True,
)

# Configuration class for backward compatibility
class Settings:
    def __init__(self):
        # Database Configuration
        self.database_url = settings.get("DATABASE_URL", 
            f"postgresql://{settings.get('POSTGRES_USER', 'postgres')}:"
            f"{settings.get('POSTGRES_PASSWORD', 'password')}@"
            f"{settings.get('POSTGRES_HOST', 'postgres')}:"
            f"{settings.get('POSTGRES_PORT', 5432)}/"
            f"{settings.get('POSTGRES_DB', 'genai_hiring')}"
        )
        
        # Redis Configuration
        self.redis_url = settings.get("REDIS_URL", 
            f"redis://{settings.get('REDIS_HOST', 'redis')}:{settings.get('REDIS_PORT', 6379)}"
        )
        
        # API Configuration
        self.api_host = settings.get("API_HOST", "0.0.0.0")
        self.api_port = settings.get("API_PORT", 8000)
        self.environment = settings.get("ENVIRONMENT", "development")
        
        # Security
        self.secret_key = settings.get("SECRET_KEY", "your-secret-key-here")
        self.jwt_secret_key = settings.get("JWT_SECRET_KEY", "your-jwt-secret-key")
        self.jwt_algorithm = settings.get("JWT_ALGORITHM", "HS256")
        self.access_token_expire_minutes = settings.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
        
        # CORS Settings
        self.allowed_origins = settings.get("ALLOWED_ORIGINS", [
            "http://localhost:3000",
            "https://yourdomain.com",
            "https://www.yourdomain.com"
        ])
        
        # File Upload Settings
        self.upload_dir = settings.get("UPLOAD_DIR", "/app/uploads")
        self.max_file_size = settings.get("MAX_FILE_SIZE", 10 * 1024 * 1024)  # 10MB
        
        # Email Configuration
        self.smtp_host = settings.get("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = settings.get("SMTP_PORT", 587)
        self.smtp_username = settings.get("SMTP_USERNAME")
        self.smtp_password = settings.get("SMTP_PASSWORD")
        self.email_from = settings.get("EMAIL_FROM")
        self.use_tls = settings.get("SMTP_USE_TLS", True)
        
        # Frontend URL
        self.frontend_url = settings.get("FRONTEND_URL", "http://localhost:3000")
        self.api_base_url = settings.get("API_BASE_URL", "http://localhost:8000")
        
        # LLM Configuration
        self.llm_model = settings.get("LLM_MODEL", "qwen2.5:3b-instruct")
        self.ollama_url = settings.get("OLLAMA_URL", "http://ollama:11434")
        
        # Google Services
        self.google_calendar_credentials_file = settings.get("GOOGLE_CALENDAR_CREDENTIALS_FILE")
        self.google_calendar_token_file = settings.get("GOOGLE_CALENDAR_TOKEN_FILE")
        
        # Application Settings
        self.shortlist_threshold = settings.get("SHORTLIST_THRESHOLD", 70)
        self.max_resume_update_attempts = settings.get("MAX_RESUME_UPDATE_ATTEMPTS", 3)
        
        # Logging
        self.log_level = settings.get("LOG_LEVEL", "INFO")
        self.log_file = settings.get("LOG_FILE", "/app/logs/app.log")

# Create global settings instance
app_settings = Settings()

# For backward compatibility
settings_instance = app_settings
```

**Create `backend/settings.toml`:**
```toml
[default]
# Default settings for all environments
API_HOST = "0.0.0.0"
API_PORT = 8000
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
MAX_FILE_SIZE = 10485760  # 10MB
UPLOAD_DIR = "/app/uploads"
SHORTLIST_THRESHOLD = 70
MAX_RESUME_UPDATE_ATTEMPTS = 3
LOG_LEVEL = "INFO"
SMTP_PORT = 587
SMTP_USE_TLS = true
LLM_MODEL = "qwen2.5:3b-instruct"

[development]
# Development environment settings
ENVIRONMENT = "development"
POSTGRES_HOST = "postgres"
REDIS_HOST = "redis"
OLLAMA_URL = "http://ollama:11434"
FRONTEND_URL = "http://localhost:3000"
API_BASE_URL = "http://localhost:8000"
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

[production]
# Production environment settings
ENVIRONMENT = "production"
POSTGRES_HOST = "postgres"
REDIS_HOST = "redis"
OLLAMA_URL = "http://ollama:11434"
# These will be overridden by environment variables
FRONTEND_URL = "https://yourdomain.com"
API_BASE_URL = "https://api.yourdomain.com"
ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://api.yourdomain.com"
]
LOG_LEVEL = "WARNING"
```

### 2.2 Frontend Environment Configuration

**Update `frontend/src/utils/config.js`:**
```javascript
// Dynamic configuration based on environment
const getConfig = () => {
  const isProduction = process.env.NODE_ENV === 'production';
  const isDevelopment = process.env.NODE_ENV === 'development';
  
  // Get the current hostname
  const hostname = window.location.hostname;
  
  // Determine API URL based on environment and hostname
  let apiUrl;
  
  if (isDevelopment) {
    // Development - use localhost or environment variable
    apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  } else if (isProduction) {
    // Production - determine based on hostname
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      apiUrl = 'http://localhost:8000';
    } else {
      // Use the same domain with api subdomain or different port
      const protocol = window.location.protocol;
      apiUrl = process.env.REACT_APP_API_URL || `${protocol}//api.${hostname}`;
    }
  } else {
    // Fallback
    apiUrl = process.env.REACT_APP_API_URL || window.location.origin.replace(':3000', ':8000');
  }

  return {
    apiUrl,
    apiHost: hostname,
    apiPort: process.env.REACT_APP_PORT || '3000',
    environment: process.env.NODE_ENV || 'development',
    isProduction,
    isDevelopment,
    version: process.env.REACT_APP_VERSION || '1.0.0',
  };
};

const config = getConfig();

export default config;
```

---

## 3. Code Changes Required

### 3.1 Backend API Changes

**Update `backend/app/main.py`:**
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
import logging
import os
from pathlib import Path

from .config import app_settings
from .database import engine, Base
from .api import (
    auth, users, companies, jobs, applications, 
    interviews, interviewer_auth, resume_update, scheduler
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, app_settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app_settings.log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="GenAI Hiring System API",
    description="AI-powered recruitment and hiring management system",
    version="1.0.0",
    docs_url="/docs" if app_settings.environment != "production" else None,
    redoc_url="/redoc" if app_settings.environment != "production" else None,
)

# Trusted Host Middleware (Security)
if app_settings.environment == "production":
    app.add_middleware(
        TrustedHostMiddleware, 
        allowed_hosts=["yourdomain.com", "*.yourdomain.com", "api.yourdomain.com"]
    )

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)

# Custom middleware for logging and monitoring
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.4f}s"
    )
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": app_settings.environment,
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }

# Static files (for uploaded resumes)
uploads_dir = Path(app_settings.upload_dir)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(companies.router, prefix="/api/companies", tags=["companies"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/applications", tags=["applications"])
app.include_router(interviews.router, prefix="/api/interviews", tags=["interviews"])
app.include_router(interviewer_auth.router, prefix="/api/interviewer", tags=["interviewer"])
app.include_router(resume_update.router, prefix="/api/resume-update", tags=["resume-update"])
app.include_router(scheduler.router, prefix="/api/scheduler", tags=["scheduler"])

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "GenAI Hiring System API",
        "version": "1.0.0",
        "docs": "/docs" if app_settings.environment != "production" else "Documentation disabled in production",
        "health": "/health"
    }

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"Starting GenAI Hiring System API in {app_settings.environment} mode")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    # Log configuration
    logger.info(f"API URL: {app_settings.api_base_url}")
    logger.info(f"Frontend URL: {app_settings.frontend_url}")
    logger.info(f"Database: {app_settings.database_url.split('@')[1] if '@' in app_settings.database_url else 'Local'}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down GenAI Hiring System API")
```

### 3.2 Update Email Templates

**Update `backend/app/utils/email.py`:**
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional
import logging
from ..config import app_settings

logger = logging.getLogger(__name__)

def send_email(
    to_emails: List[str],
    subject: str,
    body: str,
    html_body: Optional[str] = None,
    attachments: Optional[List[dict]] = None
) -> bool:
    """Send email using configured SMTP settings"""
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = app_settings.email_from
        msg['To'] = ', '.join(to_emails)
        msg['Subject'] = subject
        
        # Add body
        msg.attach(MIMEText(body, 'plain'))
        if html_body:
            msg.attach(MIMEText(html_body, 'html'))
        
        # Add attachments
        if attachments:
            for attachment in attachments:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment['content'])
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {attachment["filename"]}'
                )
                msg.attach(part)
        
        # Send email
        with smtplib.SMTP(app_settings.smtp_host, app_settings.smtp_port) as server:
            if app_settings.use_tls:
                server.starttls()
            server.login(app_settings.smtp_username, app_settings.smtp_password)
            server.send_message(msg)
        
        logger.info(f"Email sent successfully to {', '.join(to_emails)}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False

def send_application_confirmation(candidate_email: str, candidate_name: str, job_title: str, reference_number: str) -> bool:
    """Send application confirmation email with dynamic URLs"""
    
    subject = f"Application Received - {job_title} (Ref: {reference_number})"
    
    # Use dynamic URLs based on environment
    status_url = f"{app_settings.frontend_url}/application-status/{reference_number}"
    careers_url = f"{app_settings.frontend_url}/careers"
    
    body = f"""
Dear {candidate_name},

Thank you for your application for the position of {job_title}.

Your application has been successfully received and is currently being reviewed by our team.

Application Details:
- Reference Number: {reference_number}
- Position: {job_title}
- Submitted: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}

You can track your application status at: {status_url}

What happens next?
1. Our AI system will analyze your resume and qualifications
2. If you meet our initial criteria, you'll be contacted for next steps
3. We may request an updated resume if we see potential for improvement
4. Qualified candidates will be invited for interviews

We appreciate your interest in joining our team and will keep you updated throughout the process.

If you have any questions, please don't hesitate to contact us.

Best regards,
The Hiring Team

---
This is an automated message. Please do not reply to this email.
For inquiries, visit: {careers_url}
"""

    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #2563eb;">Application Received</h2>
            
            <p>Dear <strong>{candidate_name}</strong>,</p>
            
            <p>Thank you for your application for the position of <strong>{job_title}</strong>.</p>
            
            <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0; color: #1e40af;">Application Details</h3>
                <ul style="list-style: none; padding: 0;">
                    <li><strong>Reference Number:</strong> {reference_number}</li>
                    <li><strong>Position:</strong> {job_title}</li>
                    <li><strong>Submitted:</strong> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</li>
                </ul>
            </div>
            
            <p>
                <a href="{status_url}" 
                   style="background-color: #2563eb; color: white; padding: 12px 24px; 
                          text-decoration: none; border-radius: 6px; display: inline-block;">
                    Track Application Status
                </a>
            </p>
            
            <h3 style="color: #1e40af;">What happens next?</h3>
            <ol>
                <li>Our AI system will analyze your resume and qualifications</li>
                <li>If you meet our initial criteria, you'll be contacted for next steps</li>
                <li>We may request an updated resume if we see potential for improvement</li>
                <li>Qualified candidates will be invited for interviews</li>
            </ol>
            
            <p>We appreciate your interest in joining our team and will keep you updated throughout the process.</p>
            
            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
            
            <p style="font-size: 12px; color: #6b7280;">
                This is an automated message. Please do not reply to this email.<br>
                For inquiries, visit: <a href="{careers_url}">{careers_url}</a>
            </p>
        </div>
    </body>
    </html>
    """
    
    return send_email([candidate_email], subject, body, html_body)

# Update other email templates similarly...
```

### 3.3 Frontend Service Updates

**Update `frontend/src/services/api.js`:**
```javascript
import axios from 'axios';
import config from '../utils/config';

// Create axios instance with dynamic configuration
const api = axios.create({
  baseURL: config.apiUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for LLM/AI operations with longer timeout
export const llmApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 120000, // 2 minutes for LLM operations
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for file uploads with longer timeout
export const uploadApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 60000, // 1 minute for file uploads and processing
  headers: {
    'Content-Type': 'application/json',
  },
});

// Create separate axios instance for public file uploads (no auth required)
export const publicUploadApi = axios.create({
  baseURL: config.apiUrl,
  timeout: 180000, // 3 minutes for file uploads and processing (resume parsing + scoring can be slow)
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token (for regular API)
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Similar interceptors for other instances...
// (Keep existing interceptor code)

// Add environment-specific logging
if (config.isDevelopment) {
  api.interceptors.request.use(request => {
    console.log('Starting Request:', request);
    return request;
  });

  api.interceptors.response.use(
    response => {
      console.log('Response:', response);
      return response;
    },
    error => {
      console.error('API Error:', error);
      return Promise.reject(error);
    }
  );
}

export default api;
```

---

## 4. Domain and SSL Configuration

### 4.1 Nginx Configuration

**Create `nginx/nginx.conf`:**
```nginx
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    upstream frontend {
        server frontend:3000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=upload_limit:10m rate=2r/s;

    # SSL Configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Main application (yourdomain.com)
    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

        client_max_body_size 50M;

        # Frontend
        location / {
            proxy_pass http://frontend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }

        # Backend API proxy
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeout settings
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 300s;
        }

        # File uploads with special handling
        location /api/applications/apply {
            limit_req zone=upload_limit burst=5 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Extended timeouts for file processing
            proxy_connect_timeout 60s;
            proxy_send_timeout 300s;
            proxy_read_timeout 600s;
            
            client_max_body_size 50M;
        }

        # Static files (uploads)
        location /uploads/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Cache static files
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # API subdomain (api.yourdomain.com)
    server {
        listen 80;
        server_name api.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name api.yourdomain.com;

        ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;

        client_max_body_size 50M;

        # API endpoints
        location / {
            limit_req zone=api_limit burst=20 nodelay;
            
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # CORS headers for API subdomain
            add_header Access-Control-Allow-Origin "https://yourdomain.com" always;
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept, Authorization" always;
            
            if ($request_method = 'OPTIONS') {
                return 204;
            }
        }
    }
}
```

### 4.2 SSL Certificate Setup

**Create `scripts/setup-ssl.sh`:**
```bash
#!/bin/bash

# Install Certbot
apt update
apt install -y snapd
snap install core; snap refresh core
snap install --classic certbot
ln -s /snap/bin/certbot /usr/bin/certbot

# Stop nginx temporarily
docker-compose stop nginx

# Obtain SSL certificate
certbot certonly --standalone \
  --email your-email@domain.com \
  --agree-tos \
  --no-eff-email \
  -d yourdomain.com \
  -d www.yourdomain.com \
  -d api.yourdomain.com

# Set up auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'docker-compose restart nginx'" | crontab -

# Start nginx
docker-compose start nginx
```

---

## 5. Docker Configuration Updates

### 5.1 Updated docker-compose.yml

**Create `docker-compose.prod.yml`:**
```yaml
version: '3.8'

networks:
  genai-network:
    driver: bridge

services:
  postgres:
    image: postgres:15-alpine
    container_name: genai-postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-genai_hiring}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d
      - ./backups:/backups
    networks:
      - genai-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB:-genai_hiring}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  redis:
    image: redis:7-alpine
    container_name: genai-redis
    restart: unless-stopped
    volumes:
      - redis_data:/data
      - ./redis/redis.conf:/usr/local/etc/redis/redis.conf:ro
    networks:
      - genai-network
    command: redis-server /usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5
      start_period: 10s

  backend:
    build: 
      context: ./backend
      dockerfile: Dockerfile
    container_name: genai-backend
    restart: unless-stopped
    environment:
      - GENAI_ENV=production
      - DATABASE_URL=postgresql://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-genai_hiring}
      - REDIS_URL=redis://redis:6379
      - SECRET_KEY=${SECRET_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - SMTP_HOST=${SMTP_HOST}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - EMAIL_FROM=${EMAIL_FROM}
      - FRONTEND_URL=${FRONTEND_URL}
      - API_BASE_URL=${API_BASE_URL}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./uploads:/app/uploads
      - ./logs:/app/logs
      - ./backend/credentials.json:/app/credentials.json:ro
      - ./backend/token.json:/app/token.json
    networks:
      - genai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G

  frontend:
    build: 
      context: ./frontend
      dockerfile: Dockerfile.prod
    container_name: genai-frontend
    restart: unless-stopped
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=${REACT_APP_API_URL}
      - GENERATE_SOURCEMAP=false
    depends_on:
      backend:
        condition: service_healthy
    networks:
      - genai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  nginx:
    image: nginx:alpine
    container_name: genai-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - backend
      - frontend
    networks:
      - genai-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  ollama:
    image: ollama/ollama:latest
    container_name: genai-ollama
    restart: unless-stopped
    volumes:
      - ollama_data:/root/.ollama
      - ./models:/models
    networks:
      - genai-network
    environment:
      - OLLAMA_KEEP_ALIVE=24h
      - OLLAMA_HOST=0.0.0.0
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  ollama_data:
    driver: local
```

### 5.2 Production Frontend Dockerfile

**Create `frontend/Dockerfile.prod`:**
```dockerfile
# Build stage
FROM node:18-alpine as build

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built app
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Add health check
RUN apk add --no-cache curl

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost/ || exit 1

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
```

**Create `frontend/nginx.conf`:**
```nginx
server {
    listen 3000;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    # Handle React Router
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location /static/ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

---

## 6. Environment Configuration

### 6.1 Production Environment File

**Create `.env.production`:**
```bash
# Environment
GENAI_ENV=production
NODE_ENV=production
ENVIRONMENT=production

# Domain Configuration
DOMAIN=yourdomain.com
FRONTEND_URL=https://yourdomain.com
API_BASE_URL=https://api.yourdomain.com
REACT_APP_API_URL=https://api.yourdomain.com

# CORS Configuration
ALLOWED_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com","https://api.yourdomain.com"]

# Database Configuration
POSTGRES_USER=genai_user
POSTGRES_PASSWORD=your_super_secure_database_password_here
POSTGRES_DB=genai_hiring
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# Security Keys (Generate strong keys)
SECRET_KEY=your_super_secret_key_minimum_32_characters_long_production
JWT_SECRET_KEY=your_jwt_secret_key_minimum_32_characters_long_production

# Email Configuration (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_gmail_app_password_here
EMAIL_FROM=noreply@yourdomain.com
SMTP_USE_TLS=true

# File Upload Configuration
MAX_FILE_SIZE=52428800  # 50MB
UPLOAD_DIR=/app/uploads

# LLM Configuration
LLM_MODEL=qwen2.5:3b-instruct
OLLAMA_URL=http://ollama:11434

# Google Services (Optional)
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=token.json

# Application Settings
SHORTLIST_THRESHOLD=70
MAX_RESUME_UPDATE_ATTEMPTS=3

# Logging
LOG_LEVEL=WARNING
LOG_FILE=/app/logs/app.log

# Monitoring
SENTRY_DSN=your_sentry_dsn_if_using_sentry

# Backup Configuration
BACKUP_SCHEDULE=0 2 * * *  # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

---

## 7. Deployment Steps

### 7.1 Server Deployment Script

**Create `deploy.sh`:**
```bash
#!/bin/bash

set -e  # Exit on any error

echo "🚀 Starting GenAI Hiring System deployment on Contabo server..."

# Configuration
DOMAIN="yourdomain.com"
APP_DIR="/home/genai/genai-hiring-system"
BACKUP_DIR="/home/genai/backups"
LOG_FILE="/home/genai/deployment.log"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Create necessary directories
log "Creating directories..."
mkdir -p "$BACKUP_DIR"
mkdir -p "$(dirname "$LOG_FILE")"

# Update system packages
log "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Install required packages
log "Installing required packages..."
sudo apt install -y curl wget git vim htop ufw fail2ban nginx certbot python3-certbot-nginx

# Configure firewall
log "Configuring firewall..."
sudo ufw --force reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Clone or update repository
if [ -d "$APP_DIR" ]; then
    log "Updating existing repository..."
    cd "$APP_DIR"
    git pull origin main
else
    log "Cloning repository..."
    git clone https://github.com/your-username/genai-hiring-system.git "$APP_DIR"
    cd "$APP_DIR"
fi

# Copy production environment file
log "Setting up environment configuration..."
cp .env.production .env

# Update domain in configuration files
log "Updating domain configuration..."
sed -i "s/yourdomain.com/$DOMAIN/g" .env
sed -i "s/yourdomain.com/$DOMAIN/g" nginx/nginx.conf
sed -i "s/yourdomain.com/$DOMAIN/g" backend/settings.toml

# Generate strong secrets if not already set
if grep -q "your_super_secret_key" .env; then
    log "Generating security keys..."
    SECRET_KEY=$(openssl rand -base64 32)
    JWT_SECRET_KEY=$(openssl rand -base64 32)
    sed -i "s/your_super_secret_key_minimum_32_characters_long_production/$SECRET_KEY/g" .env
    sed -i "s/your_jwt_secret_key_minimum_32_characters_long_production/$JWT_SECRET_KEY/g" .env
fi

# Create required directories
log "Creating application directories..."
mkdir -p logs uploads backups database/init

# Set proper permissions
log "Setting permissions..."
sudo chown -R genai:genai "$APP_DIR"
chmod +x scripts/*.sh

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker genai
    rm get-docker.sh
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    log "Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# Stop existing services
log "Stopping existing services..."
docker-compose -f docker-compose.prod.yml down || true

# Build and start services
log "Building and starting services..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 30

# Check service health
log "Checking service health..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "Backend is healthy"
        break
    fi
    if [ $i -eq 30 ]; then
        log "ERROR: Backend failed to start"
        exit 1
    fi
    sleep 10
done

# Set up SSL certificate
log "Setting up SSL certificate..."
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    sudo certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" -d "api.$DOMAIN" --non-interactive --agree-tos --email "admin@$DOMAIN"
fi

# Set up automatic SSL renewal
log "Setting up SSL renewal..."
echo "0 12 * * * /usr/bin/certbot renew --quiet --deploy-hook 'docker-compose -f $APP_DIR/docker-compose.prod.yml restart nginx'" | sudo crontab -

# Set up database backup
log "Setting up database backup..."
cat > "$APP_DIR/scripts/backup-db.sh" << EOF
#!/bin/bash
DATE=\$(date +%Y%m%d_%H%M%S)
docker-compose -f $APP_DIR/docker-compose.prod.yml exec -T postgres pg_dump -U \${POSTGRES_USER:-postgres} \${POSTGRES_DB:-genai_hiring} > $BACKUP_DIR/db_backup_\$DATE.sql
find $BACKUP_DIR -name "db_backup_*.sql" -mtime +30 -delete
EOF

chmod +x "$APP_DIR/scripts/backup-db.sh"
echo "0 2 * * * $APP_DIR/scripts/backup-db.sh" | crontab -

# Initialize database
log "Initializing database..."
docker-compose -f docker-compose.prod.yml exec -T backend python init_db.py

# Pull and setup LLM model
log "Setting up LLM model..."
docker-compose -f docker-compose.prod.yml exec -T ollama ollama pull qwen2.5:3b-instruct

# Final health check
log "Performing final health check..."
if curl -f "https://$DOMAIN/health" > /dev/null 2>&1; then
    log "✅ Deployment successful!"
    log "🌐 Application is available at: https://$DOMAIN"
    log "🔧 API documentation: https://api.$DOMAIN/docs"
else
    log "❌ Deployment completed but health check failed"
    log "Check logs: docker-compose -f docker-compose.prod.yml logs"
fi

log "Deployment completed!"
```

### 7.2 Quick Deployment Commands

**Run these commands on your Contabo server:**

```bash
# 1. Connect to server
ssh genai@your-server-ip

# 2. Download and run deployment script
curl -sSL https://raw.githubusercontent.com/your-username/genai-hiring-system/main/deploy.sh | bash

# 3. Or manual deployment
git clone https://github.com/your-username/genai-hiring-system.git
cd genai-hiring-system
cp .env.production .env

# Edit .env with your actual values
nano .env

# Deploy
chmod +x deploy.sh
./deploy.sh
```

---

## 8. Post-Deployment Configuration

### 8.1 DNS Configuration Verification

```bash
# Verify DNS records
nslookup yourdomain.com
nslookup api.yourdomain.com
nslookup www.yourdomain.com

# Test SSL certificates
curl -I https://yourdomain.com
curl -I https://api.yourdomain.com
```

### 8.2 Application Testing

```bash
# Test API endpoints
curl https://api.yourdomain.com/health
curl https://yourdomain.com/api/health

# Test frontend
curl -I https://yourdomain.com

# Check service status
docker-compose -f docker-compose.prod.yml ps
docker-compose -f docker-compose.prod.yml logs -f
```

### 8.3 Create Admin User

```bash
# Access backend container
docker-compose -f docker-compose.prod.yml exec backend bash

# Create admin user
python -c "
from app.database import get_db
from app.models.user import User
from app.utils.auth import get_password_hash
from sqlalchemy.orm import Session

db = next(get_db())
admin_user = User(
    email='admin@yourdomain.com',
    full_name='System Administrator',
    hashed_password=get_password_hash('admin123'),
    user_type='admin',
    is_active=True
)
db.add(admin_user)
db.commit()
print('Admin user created successfully')
"
```

---

## 9. Monitoring and Maintenance

### 9.1 Monitoring Script

**Create `scripts/monitor.sh`:**
```bash
#!/bin/bash

DOMAIN="yourdomain.com"
LOG_FILE="/home/genai/monitoring.log"
ALERT_EMAIL="admin@yourdomain.com"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

send_alert() {
    echo "$1" | mail -s "GenAI System Alert" "$ALERT_EMAIL"
    log "ALERT: $1"
}

# Check website availability
if ! curl -f "https://$DOMAIN" > /dev/null 2>&1; then
    send_alert "Website https://$DOMAIN is down"
fi

# Check API availability
if ! curl -f "https://api.$DOMAIN/health" > /dev/null 2>&1; then
    send_alert "API https://api.$DOMAIN is down"
fi

# Check SSL certificate expiration
CERT_DAYS=$(echo | openssl s_client -servername "$DOMAIN" -connect "$DOMAIN:443" 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2 | xargs -I {} date -d {} +%s)
CURRENT_DATE=$(date +%s)
DAYS_UNTIL_EXPIRY=$(( (CERT_DAYS - CURRENT_DATE) / 86400 ))

if [ "$DAYS_UNTIL_EXPIRY" -lt 30 ]; then
    send_alert "SSL certificate for $DOMAIN expires in $DAYS_UNTIL_EXPIRY days"
fi

# Check disk space
DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 80 ]; then
    send_alert "Disk usage is at $DISK_USAGE%"
fi

# Check Docker containers
UNHEALTHY=$(docker ps --filter "health=unhealthy" -q | wc -l)
if [ "$UNHEALTHY" -gt 0 ]; then
    send_alert "$UNHEALTHY Docker containers are unhealthy"
fi

log "Monitoring check completed"
```

### 9.2 Maintenance Script

**Create `scripts/maintenance.sh`:**
```bash
#!/bin/bash

APP_DIR="/home/genai/genai-hiring-system"
BACKUP_DIR="/home/genai/backups"

cd "$APP_DIR"

echo "🔧 Starting maintenance tasks..."

# Update system packages
echo "📦 Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Clean up Docker
echo "🐳 Cleaning up Docker..."
docker system prune -f
docker volume prune -f

# Backup database
echo "💾 Backing up database..."
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U ${POSTGRES_USER:-postgres} ${POSTGRES_DB:-genai_hiring} > "$BACKUP_DIR/maintenance_backup_$DATE.sql"

# Update application
echo "🔄 Updating application..."
git pull origin main

# Rebuild and restart services
echo "🚀 Rebuilding services..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
echo "⏳ Waiting for services..."
sleep 30

# Health check
if curl -f "https://yourdomain.com/api/health" > /dev/null 2>&1; then
    echo "✅ Maintenance completed successfully"
else
    echo "❌ Health check failed after maintenance"
    exit 1
fi

echo "🎉 Maintenance completed!"
```

---

## 10. Troubleshooting

### 10.1 Common Issues and Solutions

#### SSL Certificate Issues
```bash
# Check certificate status
sudo certbot certificates

# Renew certificate manually
sudo certbot renew --force-renewal

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

#### Database Connection Issues
```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Connect to database manually
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d genai_hiring

# Reset database (CAUTION: This will delete all data)
docker-compose -f docker-compose.prod.yml down -v
docker-compose -f docker-compose.prod.yml up -d postgres
```

#### Application Not Loading
```bash
# Check all service logs
docker-compose -f docker-compose.prod.yml logs

# Check specific service
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml logs frontend
docker-compose -f docker-compose.prod.yml logs nginx

# Restart all services
docker-compose -f docker-compose.prod.yml restart
```

#### Email Not Working
```bash
# Test email configuration
docker-compose -f docker-compose.prod.yml exec backend python -c "
from app.utils.email import send_email
result = send_email(['test@example.com'], 'Test', 'Test message')
print('Email sent:', result)
"

# Check SMTP settings in .env file
grep SMTP .env
```

### 10.2 Performance Optimization

```bash
# Monitor resource usage
docker stats

# Optimize database
docker-compose -f docker-compose.prod.yml exec postgres psql -U postgres -d genai_hiring -c "VACUUM ANALYZE;"

# Clear application logs
find logs/ -name "*.log" -mtime +7 -delete

# Monitor disk space
df -h
du -sh uploads/
```

### 10.3 Backup and Recovery

```bash
# Create full backup
./scripts/backup-db.sh
tar -czf "full_backup_$(date +%Y%m%d).tar.gz" uploads/ logs/ .env

# Restore from backup
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres -d genai_hiring < backup_file.sql

# Restore uploads
tar -xzf full_backup_YYYYMMDD.tar.gz uploads/
```

---

## 📝 Summary Checklist

### Pre-Deployment
- [ ] Purchase domain and configure DNS
- [ ] Set up Contabo server with Ubuntu 22.04
- [ ] Install Docker and Docker Compose
- [ ] Configure firewall and security

### Code Changes
- [ ] Implement Dynaconf configuration
- [ ] Update all localhost references
- [ ] Configure CORS for production domains
- [ ] Update email templates with production URLs
- [ ] Create production Dockerfile for frontend

### Deployment
- [ ] Clone repository to server
- [ ] Configure production environment variables
- [ ] Set up SSL certificates
- [ ] Deploy with docker-compose.prod.yml
- [ ] Initialize database and create admin user

### Post-Deployment
- [ ] Test all functionality
- [ ] Set up monitoring and alerting
- [ ] Configure automated backups
- [ ] Set up maintenance schedules
- [ ] Document access credentials

### Security
- [ ] Change all default passwords
- [ ] Configure firewall rules
- [ ] Set up fail2ban for SSH protection
- [ ] Enable SSL/HTTPS everywhere
- [ ] Configure security headers

This comprehensive guide covers all aspects of deploying the GenAI Hiring System to a Contabo server with proper configuration management using Dynaconf. Follow each section carefully and customize the domain names, credentials, and other settings according to your specific requirements.
