@echo off
REM Quick script to restart MinIO container
echo Restarting MinIO container...
echo.

REM Stop and remove existing container
docker stop minio >nul 2>&1
docker rm -f minio >nul 2>&1

REM Start new container
call start-minio.bat

