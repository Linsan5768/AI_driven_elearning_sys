# Deployment Guide

This guide covers deploying the Magic Academy Learning RPG using Docker and Jenkins.

## Prerequisites

- Docker and Docker Compose installed
- Jenkins with Docker plugin
- Ollama service (for LLM) - can run separately or in Docker

## Quick Start with Docker Compose

### 1. Build and Run

```bash
# Build and start all services
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 2. Access Services

- Frontend: http://localhost
- Backend API: http://localhost:8001
- Backend Health: http://localhost:8001/api/game-state

## Jenkins Setup

### 1. Configure Jenkins

1. Install required plugins:
   - Docker Pipeline
   - Docker
   - Git

2. Configure Docker:
   - Jenkins → Manage Jenkins → Configure System
   - Add Docker installation (if needed)

3. Add credentials for Git repository (if private)

### 2. Create Jenkins Job

1. **New Item** → **Pipeline**
2. Configure:
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repository URL
   - **Script Path**: Jenkinsfile

### 3. Jenkins Pipeline Stages

The pipeline includes:

1. **Checkout**: Clone repository
2. **Build Backend**: Build backend Docker image
3. **Build Frontend**: Build frontend Docker image
4. **Test Backend**: Verify backend dependencies
5. **Test Frontend**: Verify frontend build
6. **Push to Registry** (optional): Push images to Docker registry
7. **Deploy**: Deploy using docker-compose

### 4. Environment Variables

Configure in Jenkins job:

- `DOCKER_REGISTRY` (optional): Your Docker registry URL
- Or modify `Jenkinsfile` for your specific setup

## Production Deployment

### Option 1: Docker Compose (Recommended for small deployments)

```bash
# Update docker-compose.yml with production settings
# Set environment variables
export FLASK_ENV=production

# Deploy
docker-compose up -d
```

### Option 2: Kubernetes (For larger deployments)

1. Create Kubernetes manifests:
   - `k8s/backend-deployment.yaml`
   - `k8s/frontend-deployment.yaml`
   - `k8s/service.yaml`

2. Apply configurations:
   ```bash
   kubectl apply -f k8s/
   ```

### Option 3: Separate Docker Containers

```bash
# Backend
cd backend
docker build -t magic-academy-backend:latest .
docker run -d -p 8001:8001 \
  -v $(pwd)/uploads:/app/uploads \
  -v $(pwd)/courses:/app/courses \
  --name backend \
  magic-academy-backend:latest

# Frontend
cd frontend
docker build -t magic-academy-frontend:latest .
docker run -d -p 80:80 \
  --name frontend \
  magic-academy-frontend:latest
```

## Environment Configuration

### Backend Environment Variables

Create `.env` file in `backend/` (or set in docker-compose.yml):

```env
FLASK_ENV=production
FLASK_DEBUG=0
PORT=8001
```

### Frontend Environment Variables

The frontend uses hardcoded API URL. For production:

1. Create `.env` file in `frontend/`:
   ```env
   VITE_API_BASE_URL=http://your-backend-url:8001
   ```

2. Update `frontend/src/App.tsx` to use:
   ```typescript
   const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001/api'
   ```

## Ollama Integration

Ollama can run:

1. **Separately on host**: Install Ollama on host machine
2. **In Docker**: Add to docker-compose.yml:
   ```yaml
   ollama:
     image: ollama/ollama:latest
     ports:
       - "11434:11434"
     volumes:
       - ollama_data:/root/.ollama
   ```

3. **Update frontend API calls** to use `http://ollama:11434` when in Docker network

## Volume Persistence

Important volumes to persist:

- `backend/uploads/`: Uploaded course files
- `backend/courses/`: Generated course JSON files
- `ollama_data/`: Ollama model cache (if using Docker Ollama)

Update docker-compose.yml to use named volumes:

```yaml
volumes:
  uploads_data:
  courses_data:
  ollama_data:
```

## Health Checks

Add health checks to docker-compose.yml:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/api/game-state"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Monitoring

Consider adding:

- **Logging**: Configure log aggregation (ELK, Loki, etc.)
- **Metrics**: Prometheus + Grafana
- **Health endpoints**: Already available at `/api/game-state`

## Troubleshooting

### Backend not responding

```bash
# Check logs
docker-compose logs backend

# Check if port is in use
lsof -i :8001

# Restart service
docker-compose restart backend
```

### Frontend build fails

```bash
# Clear build cache
docker-compose build --no-cache frontend

# Check Node version compatibility
docker run --rm node:18-alpine node --version
```

### Images not updating

```bash
# Force rebuild
docker-compose build --no-cache

# Remove old images
docker-compose down --rmi local
```

## Security Considerations

1. **API Keys**: Use environment variables or secrets management
2. **HTTPS**: Configure reverse proxy (nginx/traefik) with SSL
3. **Firewall**: Restrict backend port (8001) to internal network only
4. **Secrets**: Use Docker secrets or Kubernetes secrets for sensitive data

## Backup Strategy

Backup important data:

```bash
# Backup courses and uploads
docker run --rm \
  -v magic-academy_backend_uploads:/data/uploads \
  -v magic-academy_backend_courses:/data/courses \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/magic-academy-$(date +%Y%m%d).tar.gz /data
```

## CI/CD Best Practices

1. **Tag images** with version numbers or commit SHAs
2. **Run tests** before building images
3. **Scan images** for vulnerabilities (Trivy, Snyk)
4. **Rolling updates**: Use Kubernetes or orchestration tool
5. **Blue-green deployment**: For zero-downtime updates

