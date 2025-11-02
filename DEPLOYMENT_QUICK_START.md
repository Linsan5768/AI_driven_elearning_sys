# Quick Deployment Guide

## Docker Compose (Recommended)

### 1. Build and Start

```bash
# Clone repository
git clone <your-repo-url>
cd demo

# Build and start services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Access Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8001

### 3. Configure Ollama (Required for LLM features)

Ollama must be running separately:

```bash
# Install Ollama (if not installed)
# Visit https://ollama.ai for installation

# Start Ollama service
ollama serve

# Pull required models
ollama pull qwen2.5:7b
ollama pull llama2
```

If Ollama runs on a different host, update frontend environment:
- Edit `docker-compose.yml` → `frontend.build.args.VITE_OLLAMA_URL`

## Jenkins Setup

### 1. Install Jenkins Plugins

- Docker Pipeline
- Docker
- Git

### 2. Create Pipeline Job

1. Jenkins → **New Item** → **Pipeline**
2. **Definition**: Pipeline script from SCM
3. **SCM**: Git
4. **Repository URL**: Your Git repo
5. **Script Path**: `Jenkinsfile`

### 3. Run Pipeline

- Click **Build Now**
- Pipeline will:
  - Build backend and frontend Docker images
  - Run basic tests
  - Deploy using docker-compose (on main/master branch)

## Manual Docker Build

### Backend

```bash
cd backend
docker build -t magic-academy-backend:latest .
docker run -d -p 8001:8001 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/courses:/app/courses \
  --name backend \
  magic-academy-backend:latest
```

### Frontend

```bash
cd frontend
docker build -t magic-academy-frontend:latest \
  --build-arg VITE_API_BASE_URL=http://localhost:8001/api \
  .
docker run -d -p 80:80 --name frontend magic-academy-frontend:latest
```

## Environment Variables

### Backend (.env or docker-compose.yml)

```env
FLASK_ENV=production
FLASK_DEBUG=False
PORT=8001
```

### Frontend (Build-time)

Set via Docker build args or `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8001/api
VITE_OLLAMA_URL=http://127.0.0.1:11434
```

## Troubleshooting

### Backend not responding

```bash
docker-compose logs backend
docker-compose restart backend
```

### Frontend shows API errors

- Check backend is running: `curl http://localhost:8001/api/game-state`
- Verify `VITE_API_BASE_URL` in frontend build

### Ollama connection failed

- Ensure Ollama is running: `curl http://127.0.0.1:11434/api/tags`
- If in Docker, use `http://ollama:11434` (service name)

## Production Considerations

1. **HTTPS**: Use reverse proxy (nginx/traefik) with SSL
2. **Database**: Consider PostgreSQL for production data
3. **Caching**: Add Redis for session/data caching
4. **Monitoring**: Set up health checks and logging
5. **Backup**: Automate backups of `uploads/` and `courses/` directories

