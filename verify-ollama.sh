#!/bin/bash
# Quick verification script for Ollama Docker setup

echo "🔍 Verifying Ollama Docker Setup"
echo "=================================="

# Check if Docker is running
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi
echo "✅ Docker is running"

# Check if Ollama container exists
if ! docker ps -a | grep -q magic-academy-ollama; then
    echo "⚠️  Ollama container not found. Start it with: docker-compose up -d"
    exit 1
fi

# Check if Ollama container is running
if docker ps | grep -q magic-academy-ollama; then
    echo "✅ Ollama container is running"
else
    echo "⚠️  Ollama container exists but is not running"
    echo "   Start it with: docker start magic-academy-ollama"
    exit 1
fi

# Check if models are available
echo ""
echo "📦 Checking Ollama models..."
MODELS=$(docker exec magic-academy-ollama ollama list 2>/dev/null | grep -E "qwen2.5|llama2" | wc -l)
if [ "$MODELS" -gt 0 ]; then
    echo "✅ Models found:"
    docker exec magic-academy-ollama ollama list 2>/dev/null | grep -E "qwen2.5|llama2" || true
else
    echo "⚠️  No models found. Pull them with:"
    echo "   docker exec magic-academy-ollama ollama pull qwen2.5:7b"
    echo "   docker exec magic-academy-ollama ollama pull llama2"
fi

# Test Ollama API via proxy
echo ""
echo "🌐 Testing Ollama API..."
if curl -s http://localhost/ollama/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama proxy (/ollama) is working"
else
    echo "⚠️  Ollama proxy not accessible. Check frontend container."
fi

# Test Ollama API directly
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama direct access (port 11434) is working"
else
    echo "⚠️  Ollama direct access not working. Check Ollama container."
fi

# Test backend access to Ollama
echo ""
echo "🔗 Testing backend access to Ollama..."
if docker exec magic-academy-backend curl -s http://ollama:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Backend can access Ollama via Docker network"
else
    echo "⚠️  Backend cannot access Ollama. Check network configuration."
fi

echo ""
echo "=================================="
echo "✨ Verification complete!"
echo ""
echo "If all checks passed, Ollama is ready to use!"
echo "If some checks failed, see OLLAMA_DOCKER_SETUP.md for troubleshooting."

