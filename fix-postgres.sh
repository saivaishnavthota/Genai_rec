#!/bin/bash

echo "Stopping all containers..."
docker-compose down

echo "Starting only PostgreSQL to attempt recovery..."
docker-compose up -d postgres

echo "Waiting for PostgreSQL to start..."
sleep 10

echo "Checking PostgreSQL logs..."
docker-compose logs postgres

echo "Testing PostgreSQL connection..."
docker exec genai-postgres pg_isready -U postgres -d genai_hiring

echo "If successful, start all services:"
echo "docker-compose up -d"
