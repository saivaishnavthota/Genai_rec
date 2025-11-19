# Quick Reference - GenAI Hiring System

## 🚀 System Status: OPERATIONAL

All services are running and healthy!

---

## 📊 Service Access

| Service | URL | Status | Purpose |
|---------|-----|--------|---------|
| **Frontend** | http://localhost:6003 | ✅ | React Application |
| **Backend API** | http://localhost:6002 | ✅ | FastAPI REST API |
| **API Docs** | http://localhost:6002/docs | ✅ | Interactive API Documentation |
| **PostgreSQL** | localhost:6000 | ✅ | Database |
| **Redis** | localhost:6001 | ✅ | Cache & Sessions |
| **Ollama LLM** | localhost:6004 | ✅ | AI Model (qwen2.5:3b) |

---

## 🔧 Docker Commands

```bash
# View all services
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Restart a service
docker-compose restart [service-name]

# Stop all services
docker-compose down

# Start all services (including Ollama)
docker-compose --profile ollama up -d

# Rebuild a service
docker-compose build [service-name]

# Access container shell
docker-compose exec [service-name] sh
```

---

## 🧪 Quick Tests

```bash
# Test Backend Health
curl http://localhost:6002/health

# Test Frontend
curl -I http://localhost:6003

# Test Ollama
curl http://localhost:6004/api/version

# Check Ollama Models
curl http://localhost:6004/api/tags

# Test API Root
curl http://localhost:6002/
```

---

## 📝 Key Endpoints

### Authentication
- POST `/api/auth/login` - User login
- POST `/api/auth/register` - User registration
- GET `/api/auth/me` - Current user info

### Jobs (Public)
- GET `/api/jobs/public` - List published jobs
- GET `/api/jobs/public/{id}` - Job details

### Applications (Public)
- POST `/api/applications/apply` - Submit application
- GET `/api/applications/reference/{ref}` - Check status

### AI Features
- POST `/api/jobs/generate-fields` - AI job fields
- POST `/api/jobs/generate-description` - AI job description
- POST `/api/applications/{id}/rescore` - AI rescoring

---

## 📚 Documentation Files

1. **ENDPOINTS_ANALYSIS.md** - Complete API documentation (60+ endpoints)
2. **SYSTEM_STATUS_REPORT.md** - Detailed system analysis
3. **QUICK_REFERENCE.md** - This file
4. **README.md** - Project overview
5. **PROJECT_SUMMARY.md** - Project summary

---

## 🔑 User Roles

| Role | Permissions |
|------|------------|
| **admin** | Full system access |
| **hr** | Company-wide HR operations, approve/publish jobs |
| **account_manager** | Create jobs, manage applications |
| **interviewer** | Token-based review submission (no account) |

---

## 🗂️ Project Structure

```
GENAI-main/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/      # API endpoints
│   │   ├── models/   # Database models
│   │   ├── services/ # Business logic
│   │   └── utils/    # Utilities
│   └── requirements.txt
├── frontend/         # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── context/
│   └── package.json
├── database/         # Database init scripts
├── docker-compose.yml
└── Documentation files
```

---

## ⚙️ Environment Variables

### Backend (.env)
```env
DATABASE_URL=postgresql://postgres:password@postgres:5432/genai_hiring
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key
FRONTEND_URL=http://localhost:3000
USE_OLLAMA=true
OLLAMA_BASE_URL=http://ollama:11434
SMTP_HOST=smtp.gmail.com
SMTP_USERNAME=your-email
SMTP_PASSWORD=your-password
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_ENVIRONMENT=development
```

---

## 🔄 Application Workflow

### Job Posting Flow
1. Account Manager creates job → `POST /api/jobs/`
2. HR approves job → `PATCH /api/jobs/{id}/approve`
3. HR publishes job → `PATCH /api/jobs/{id}/publish`
4. Job appears on careers page → `GET /api/jobs/public`

### Application Flow
1. Candidate submits application → `POST /api/applications/apply`
2. AI scores resume automatically
3. HR reviews applications → `GET /api/applications/`
4. HR shortlists/rejects → `PATCH /api/applications/{id}/status`

### Interview Flow
1. HR fetches availability → `POST /api/interviews/fetch-availability/{id}`
2. Candidate selects slot → `POST /api/interviews/select-slot/{id}`
3. HR schedules interview → `POST /api/interviews/schedule-interview/{id}`
4. Interview conducted
5. HR marks complete → `PATCH /api/interviews/mark-completed/{id}`
6. Interviewers submit reviews → `POST /api/interviewer/submit-review/{token}`
7. HR makes final decision → `PATCH /api/applications/{id}/final-decision`

---

## 🚨 Troubleshooting

### Frontend won't start
```bash
docker-compose exec -u root frontend npm install
docker-compose restart frontend
```

### Backend database error
```bash
docker-compose restart postgres
docker-compose restart backend
```

### Ollama not responding
```bash
docker-compose restart ollama
# Wait 30 seconds
curl http://localhost:6004/api/version
```

### Clear all data and restart
```bash
docker-compose down -v
docker-compose --profile ollama up -d
```

---

## 📈 Performance Notes

| Operation | Timeout | Notes |
|-----------|---------|-------|
| Standard API | 10s | User/job operations |
| LLM Operations | 120s | AI generation/scoring |
| File Upload (Auth) | 60s | Resume processing |
| File Upload (Public) | 180s | Application submission |

---

## 🔐 Security Checklist

- [x] JWT authentication enabled
- [x] Role-based access control
- [x] Password hashing (bcrypt)
- [x] CORS protection
- [x] File type validation
- [x] SQL injection protection (ORM)
- [ ] HTTPS (production)
- [ ] Rate limiting
- [ ] CSRF protection

---

## 📞 Support

For issues or questions:
1. Check logs: `docker-compose logs [service-name]`
2. Review documentation in this directory
3. Check API docs: http://localhost:6002/docs

---

**Last Updated:** October 14, 2025

