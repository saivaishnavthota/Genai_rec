# GenAI Hiring System - Complete Setup Guide

## 📋 Prerequisites

Before starting, ensure you have the following installed on your system:

### Required Software

1. **Docker Desktop** (Recommended)
   - **Windows**: Download from [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
   - **macOS**: Download from [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)
   - **Linux**: Install Docker Engine and Docker Compose separately

2. **Git** (for cloning the repository)
   - **Windows**: Download from [Git for Windows](https://git-scm.com/download/win)
   - **macOS**: Install via Homebrew: `brew install git`
   - **Linux**: Install via package manager: `sudo apt install git`

3. **Web Browser** (Chrome, Firefox, Safari, or Edge)

### System Requirements

- **RAM**: Minimum 8GB, Recommended 16GB
- **Storage**: At least 10GB free space
- **CPU**: Multi-core processor recommended
- **Network**: Internet connection for Docker images and dependencies

## 🚀 Quick Setup (Automated)

### Option 1: Windows Quick Start

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd genai-hiring-system
   ```

2. **Run the Automated Setup**
   ```bash
   # Double-click or run from command prompt
   start.bat
   ```

3. **Follow the Prompts**
   - The script will check Docker installation
   - Create necessary directories and configuration files
   - Build and start all services automatically
   - Open the application in your browser

### Option 2: Linux/macOS Quick Start

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd genai-hiring-system
   ```

2. **Make Script Executable and Run**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. **Follow the Prompts**
   - Configure the .env file when prompted
   - Wait for all services to start
   - Access the application at http://localhost:3000

## 🔧 Manual Setup (Step-by-Step)

If you prefer manual setup or encounter issues with automated scripts:

### Step 1: Environment Configuration

1. **Create Environment File**
   ```bash
   cp env.example .env
   ```

2. **Edit .env File**
   ```bash
   # Database Configuration
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_DB=genai_hiring
   POSTGRES_PORT=5432

   # Redis Configuration
   REDIS_PORT=6379

   # Backend Configuration
   BACKEND_PORT=8000
   SECRET_KEY=your-super-secret-key-here
   JWT_SECRET_KEY=your-jwt-secret-key

   # Frontend Configuration
   FRONTEND_PORT=3000
   REACT_APP_API_URL=http://localhost:8000

   # Email Configuration (Required for notifications)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAIL_FROM=your-email@gmail.com

   # Google Calendar/Meet Integration (Optional)
   GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
   GOOGLE_CALENDAR_TOKEN_FILE=token.json

   # LLM Configuration
   OLLAMA_PORT=11434
   LLM_MODEL=qwen2.5:3b-instruct
   ```

### Step 2: Create Required Directories

```bash
# Create necessary directories
mkdir -p logs uploads database/init database/backups
```

### Step 3: Docker Services Setup

1. **Build and Start Services**
   ```bash
   # Pull latest images
   docker-compose pull

   # Build custom images
   docker-compose build --no-cache

   # Start all services
   docker-compose up -d
   ```

2. **Verify Services are Running**
   ```bash
   # Check service status
   docker-compose ps

   # Check service health
   docker-compose logs -f
   ```

### Step 4: Database Initialization

1. **Wait for PostgreSQL to be Ready**
   ```bash
   # Wait for database to be healthy
   docker-compose exec postgres pg_isready -U postgres
   ```

2. **Initialize Database Tables**
   ```bash
   # Run database initialization
   docker-compose exec backend python init_db.py
   ```

3. **Create Sample Data (Optional)**
   ```bash
   # Create sample job and users
   docker-compose exec backend python create_sample_job.py
   ```

### Step 5: Verify Installation

1. **Check Service Health**
   - Backend API: http://localhost:8000/health
   - Frontend App: http://localhost:3000
   - API Documentation: http://localhost:8000/docs

2. **Test User Registration**
   - Navigate to http://localhost:3000
   - Register a new user account
   - Verify email functionality (if configured)

## ⚙️ Advanced Configuration

### Email Setup (Gmail Example)

1. **Enable 2-Factor Authentication** on your Gmail account

2. **Generate App Password**
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate password for "Mail"

3. **Update .env Configuration**
   ```bash
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-character-app-password
   EMAIL_FROM=your-email@gmail.com
   ```

### Google Calendar/Meet Integration

1. **Create Google Cloud Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create new project or select existing one

2. **Enable APIs**
   - Enable Google Calendar API
   - Enable Google Meet API (if available)

3. **Create Service Account**
   - Go to IAM & Admin → Service Accounts
   - Create new service account
   - Download JSON credentials file

4. **Configure OAuth (Alternative)**
   ```bash
   # Run OAuth setup script
   docker-compose exec backend python setup_google_calendar_oauth.py
   ```

5. **Update Configuration**
   ```bash
   # Copy credentials file to backend directory
   cp path/to/credentials.json backend/credentials.json

   # Update .env file
   GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
   ```

### LLM Model Setup (Ollama)

1. **Start Ollama Service**
   ```bash
   # Start with Ollama profile
   docker-compose --profile ollama up -d
   ```

2. **Pull Required Model**
   ```bash
   # Pull the AI model
   docker-compose exec ollama ollama pull qwen2.5:3b-instruct
   ```

3. **Verify Model Installation**
   ```bash
   # List installed models
   docker-compose exec ollama ollama list
   ```

### SSL/HTTPS Setup (Production)

1. **Obtain SSL Certificates**
   - Use Let's Encrypt with Certbot
   - Or use your domain provider's SSL certificates

2. **Configure Reverse Proxy**
   - Add Nginx service to docker-compose.yml
   - Configure SSL termination

3. **Update Environment Variables**
   ```bash
   FRONTEND_URL=https://yourdomain.com
   REACT_APP_API_URL=https://api.yourdomain.com
   ```

## 🔍 Troubleshooting

### Common Issues and Solutions

#### 1. Docker Issues

**Problem**: Docker Desktop not starting
```bash
# Solution: Restart Docker Desktop
# Windows: Restart Docker Desktop application
# Linux: sudo systemctl restart docker
```

**Problem**: Port conflicts
```bash
# Solution: Change ports in .env file
FRONTEND_PORT=3001
BACKEND_PORT=8001
POSTGRES_PORT=5433
```

#### 2. Database Issues

**Problem**: Database connection failed
```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

**Problem**: Database initialization failed
```bash
# Manually run initialization
docker-compose exec backend python init_db.py

# Check database tables
docker-compose exec postgres psql -U postgres -d genai_hiring -c "\dt"
```

#### 3. Frontend Issues

**Problem**: Frontend not loading
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose build --no-cache frontend
docker-compose up -d frontend
```

**Problem**: API connection issues
```bash
# Verify backend is running
curl http://localhost:8000/health

# Check network connectivity
docker-compose exec frontend ping backend
```

#### 4. Backend Issues

**Problem**: Backend API not responding
```bash
# Check backend logs
docker-compose logs backend

# Restart backend service
docker-compose restart backend

# Check Python dependencies
docker-compose exec backend pip list
```

**Problem**: Email not working
```bash
# Test email configuration
docker-compose exec backend python -c "
from app.utils.email import send_email
result = send_email(['test@example.com'], 'Test', 'Test message')
print('Email sent:', result)
"
```

#### 5. Performance Issues

**Problem**: Slow application response
```bash
# Check resource usage
docker stats

# Increase memory limits in docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

### Log Analysis

1. **View All Logs**
   ```bash
   docker-compose logs -f
   ```

2. **View Specific Service Logs**
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f frontend
   docker-compose logs -f postgres
   ```

3. **Filter Logs by Time**
   ```bash
   docker-compose logs --since=1h backend
   docker-compose logs --until=2023-01-01 frontend
   ```

### Health Monitoring

1. **Service Health Checks**
   ```bash
   # Backend health
   curl http://localhost:8000/health

   # Database health
   docker-compose exec postgres pg_isready -U postgres

   # Redis health
   docker-compose exec redis redis-cli ping
   ```

2. **Resource Monitoring**
   ```bash
   # Container resource usage
   docker stats

   # Disk usage
   docker system df

   # Clean up unused resources
   docker system prune -a
   ```

## 🚀 Production Deployment

### Environment Preparation

1. **Server Requirements**
   - Ubuntu 20.04+ or CentOS 8+
   - 16GB RAM minimum
   - 100GB storage minimum
   - Docker and Docker Compose installed

2. **Security Configuration**
   ```bash
   # Update system packages
   sudo apt update && sudo apt upgrade -y

   # Configure firewall
   sudo ufw allow 22    # SSH
   sudo ufw allow 80    # HTTP
   sudo ufw allow 443   # HTTPS
   sudo ufw enable

   # Create application user
   sudo useradd -m -s /bin/bash genai
   sudo usermod -aG docker genai
   ```

3. **Production Environment Variables**
   ```bash
   # Production .env configuration
   ENVIRONMENT=production
   SECRET_KEY=super-secure-production-key
   JWT_SECRET_KEY=super-secure-jwt-key
   POSTGRES_PASSWORD=very-secure-database-password

   # Use production URLs
   FRONTEND_URL=https://yourdomain.com
   REACT_APP_API_URL=https://api.yourdomain.com

   # Production email settings
   SMTP_HOST=your-production-smtp-server
   SMTP_USERNAME=noreply@yourdomain.com
   SMTP_PASSWORD=production-email-password
   ```

### Backup and Recovery

1. **Database Backup**
   ```bash
   # Create backup script
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   docker-compose exec -T postgres pg_dump -U postgres genai_hiring > backup_$DATE.sql
   ```

2. **File Backup**
   ```bash
   # Backup uploaded files
   tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/
   ```

3. **Automated Backups**
   ```bash
   # Add to crontab
   0 2 * * * /path/to/backup_script.sh
   ```

### Monitoring and Maintenance

1. **Log Rotation**
   ```bash
   # Configure log rotation
   sudo nano /etc/logrotate.d/genai-hiring
   ```

2. **Health Monitoring**
   ```bash
   # Create monitoring script
   #!/bin/bash
   if ! curl -f http://localhost:8000/health; then
       docker-compose restart backend
       # Send alert email
   fi
   ```

3. **Regular Maintenance**
   ```bash
   # Weekly maintenance script
   docker system prune -f
   docker-compose pull
   docker-compose up -d --remove-orphans
   ```

## 📞 Support and Maintenance

### Getting Help

1. **Check Documentation**
   - Review this setup guide
   - Check project_summary.md for workflow details
   - Review Docker Compose logs

2. **Common Commands**
   ```bash
   # Restart all services
   docker-compose restart

   # Update to latest version
   git pull origin main
   docker-compose build --no-cache
   docker-compose up -d

   # View real-time logs
   docker-compose logs -f

   # Stop all services
   docker-compose down

   # Complete reset (removes all data)
   docker-compose down -v
   docker system prune -a
   ```

### Maintenance Schedule

1. **Daily Tasks**
   - Monitor service health
   - Check error logs
   - Verify backup completion

2. **Weekly Tasks**
   - Update Docker images
   - Clean up old logs
   - Review performance metrics

3. **Monthly Tasks**
   - Security updates
   - Database optimization
   - Capacity planning review

This comprehensive setup guide should help you get the GenAI Hiring System running in any environment. For additional support or custom configurations, refer to the individual service documentation or contact the development team.

