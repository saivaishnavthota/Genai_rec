#!/bin/bash

echo "🚀 Starting GenAI Hiring System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "⚠️  Please edit .env file with your configuration before proceeding!"
    echo "🔧 Required: Database credentials, OpenAI API key, Email settings"
    read -p "Press Enter after configuring .env file..."
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "🐳 Starting services with Docker Compose..."
docker-compose up --build -d

echo "⏳ Waiting for services to start..."
sleep 30

echo "🏥 Checking service health..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend is not responding"
fi

if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo "✅ Frontend is healthy"
else
    echo "❌ Frontend is not responding"
fi

echo ""
echo "🎉 GenAI Hiring System is ready!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "👥 Test Users (after database setup):"
echo "   Account Manager: manager@example.com"
echo "   HR: hr@example.com"
echo "   Admin: admin@example.com"
echo "   Password: password123"
echo ""
echo "📋 To view logs: docker-compose logs -f"
echo "🛑 To stop: docker-compose down"
