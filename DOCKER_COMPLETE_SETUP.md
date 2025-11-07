# Run Complete Application on Docker

## ✅ Yes! You can run the complete application on Docker

All services are configured in `docker-compose.yml`:
- ✅ PostgreSQL Database
- ✅ Redis Cache
- ✅ MinIO Storage
- ✅ Backend API (FastAPI)
- ✅ Frontend (React)

## 🚀 Quick Start

### 1. Prerequisites
- Docker Desktop installed and running
- Docker Compose installed (comes with Docker Desktop)

### 2. Create Environment File
Copy `env.example` to `.env` and update values:
```cmd
copy env.example .env
```

**Important:** Update these for Docker:
```env
# Database (already correct for Docker)
DATABASE_URL=postgresql://postgres:vaishnav@postgres:5432/genai_hiring

# Redis (already correct for Docker)
REDIS_URL=redis://redis:6379

# MinIO (for Docker, backend will use service name)
MINIO_ENDPOINT=minio:9000

# Frontend API URL (use localhost for browser access)
REACT_APP_API_URL=http://localhost:8000
```

### 3. Start All Services
```cmd
docker-compose up -d
```

This will:
- Build backend and frontend images
- Start all services in the background
- Wait for health checks to pass

### 4. View Logs
```cmd
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### 5. Stop All Services
```cmd
docker-compose down
```

### 6. Stop and Remove Volumes (Clean Slate)
```cmd
docker-compose down -v
```

## 📋 Service URLs

Once running, access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **MinIO Console**: http://localhost:9001
  - Login: `minioadmin` / `minioadmin`
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🔧 Common Commands

### Start specific services
```cmd
docker-compose up -d postgres redis minio
docker-compose up -d backend
docker-compose up -d frontend
```

### Restart a service
```cmd
docker-compose restart backend
docker-compose restart frontend
```

### Rebuild after code changes
```cmd
# Rebuild and restart
docker-compose up -d --build backend
docker-compose up -d --build frontend

# Rebuild all
docker-compose up -d --build
```

### View running containers
```cmd
docker-compose ps
```

### Execute commands in containers
```cmd
# Backend shell
docker-compose exec backend bash

# Run migrations
docker-compose exec backend alembic upgrade head

# Frontend shell
docker-compose exec frontend sh
```

## 🐛 Troubleshooting

### Port Already in Use
If ports are already in use:
```cmd
# Check what's using the port
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill the process or change ports in docker-compose.yml
```

### Services Won't Start
1. Check logs:
   ```cmd
   docker-compose logs
   ```

2. Check Docker Desktop is running

3. Check disk space:
   ```cmd
   docker system df
   ```

### Frontend Can't Connect to Backend
- Ensure `REACT_APP_API_URL=http://localhost:8000` in `.env`
- Backend must be accessible from your host machine
- Check backend logs: `docker-compose logs backend`

### Database Connection Issues
- Ensure PostgreSQL is healthy: `docker-compose ps postgres`
- Check connection string uses `postgres` (service name) not `localhost`

### MinIO Not Working
- Check MinIO is running: `docker-compose ps minio`
- Access console: http://localhost:9001
- Backend uses `minio:9000` (service name) internally
- External access uses `localhost:9000`

## 📝 Development vs Production

### Development Mode (Current)
- Hot reload enabled
- Source code mounted as volumes
- Development dependencies included
- Debug logging enabled

### Production Mode
To run in production:
1. Update `ENVIRONMENT=production` in `.env`
2. Build production images:
   ```cmd
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
   ```
   (You may need to create `docker-compose.prod.yml`)

## 🔄 Updating Code

### Backend Changes
Code changes are automatically reflected (volume mount). For new dependencies:
```cmd
docker-compose exec backend pip install -r requirements.txt
docker-compose restart backend
```

### Frontend Changes
Code changes are automatically reflected (volume mount). For new dependencies:
```cmd
docker-compose exec frontend npm install
docker-compose restart frontend
```

## 📊 Monitoring

### Check Service Health
```cmd
docker-compose ps
```

All services should show "healthy" status.

### Resource Usage
```cmd
docker stats
```

## 🗑️ Cleanup

### Remove Everything
```cmd
# Stop and remove containers, networks
docker-compose down

# Also remove volumes (⚠️ deletes database data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 📚 Additional Notes

### Ollama (LLM)
- Ollama runs **locally** (not in Docker) by default
- Backend connects via `host.docker.internal:11434`
- To use Docker Ollama, uncomment the ollama service in `docker-compose.yml`

### Persistent Data
- Database data: `postgres_data` volume
- Redis data: `redis_data` volume
- MinIO data: `minio_data` volume
- Uploads: `./uploads` directory (mounted)

### Network
All services are on `genai-network` and can communicate using service names:
- `postgres:5432`
- `redis:6379`
- `minio:9000`
- `backend:8000`
- `frontend:3000`

## ✅ Verification Checklist

After starting, verify:
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend API accessible at http://localhost:8000/docs
- [ ] Database connection works (check backend logs)
- [ ] Redis connection works (check backend logs)
- [ ] MinIO console accessible at http://localhost:9001
- [ ] All services show "healthy" in `docker-compose ps`

## 🎉 You're All Set!

Your complete application is now running on Docker. All services are connected and ready to use.

