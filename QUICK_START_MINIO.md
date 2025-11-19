# Quick Start - MinIO

## How to Run the Script

### From Project Root (Recommended)
```cmd
cd C:\Users\saiva\Desktop\genai-hiring-system\GENAI-main
start-minio.bat
```

Or if you're already in the project root:
```cmd
.\start-minio.bat
```

### From Any Directory
```cmd
cd C:\Users\saiva\Desktop\genai-hiring-system\GENAI-main
start-minio.bat
```

## Step-by-Step Process

### 1. Check Docker Desktop
First, make sure Docker Desktop is running:
```cmd
check-docker.bat
```

Or manually:
```cmd
docker ps
```

If Docker is not running:
- Start Docker Desktop from Start Menu
- Wait for it to fully initialize (check system tray)
- Docker icon should show "Docker Desktop is running"

### 2. Start MinIO
Once Docker Desktop is running:
```cmd
cd C:\Users\saiva\Desktop\genai-hiring-system\GENAI-main
start-minio.bat
```

## What the Script Does

1. ✅ Checks if Docker Desktop is running
2. ✅ Finds and removes any existing MinIO container
3. ✅ Starts a fresh MinIO container
4. ✅ Shows connection information

## Expected Output

```
========================================
MinIO Container Management
========================================

[0/4] Checking Docker availability...
   Docker is available.

[1/4] Checking for existing MinIO container...
   Found existing MinIO container.

[2/4] Stopping and removing existing container...
   Container removed successfully.

[3/4] Starting new MinIO container...

[4/4] Verifying container is running...
   Container is running.

========================================
MinIO started successfully!
========================================

Access MinIO Console at: http://localhost:9001
Login: minioadmin / minioadmin

API Endpoint: http://localhost:9000
```

## Access MinIO

After starting:
- **Console**: http://localhost:9001 (minioadmin/minioadmin)
- **API**: http://localhost:9000

## Troubleshooting

### Script Not Found
Make sure you're in the project root directory:
```cmd
cd C:\Users\saiva\Desktop\genai-hiring-system\GENAI-main
```

### Docker Not Running
Run `check-docker.bat` first, or start Docker Desktop manually.

### Port Already in Use
Check if ports 9000/9001 are in use:
```cmd
netstat -an | findstr "9000 9001"
```

