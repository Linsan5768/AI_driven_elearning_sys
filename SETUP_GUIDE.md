# Magic Academy - Complete Setup Guide

> **Complete step-by-step guide for setting up the project after pulling from Git**

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Detailed Setup Steps](#detailed-setup-steps)
- [Docker Deployment](#docker-deployment)
- [Jenkins CI/CD](#jenkins-cicd)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## 🚀 Quick Start

### Prerequisites

Ensure you have installed:

- ✅ **Docker Desktop** (Required)
- ✅ **Git** (Required)
- ✅ **Node.js 18+** (Only for local development mode)
- ✅ **Python 3.9+** (Only for local development mode)

> 💡 **Note**: If using Docker deployment, you **do NOT need** to install Ollama, Node.js, or Python locally!

### One-Command Setup (Docker - Recommended)

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd demo

# 2. Start all services (including Ollama)
docker-compose up -d --build

# 3. Pull Ollama models (first time only)
docker exec magic-academy-ollama ollama pull qwen2.5:7b
docker exec magic-academy-ollama ollama pull llama2

# 4. Access the application
# Frontend: http://localhost
# Backend: http://localhost:8001
```

---

## 📝 Detailed Setup Steps

### Step 1: Clone Repository

```bash
# Clone the repository
git clone <your-repo-url>
cd demo

# Verify file structure
ls -la
# Should see: backend/, frontend/, docker-compose.yml, Jenkinsfile, etc.
```

### Step 2: Choose Deployment Method

#### Option A: Docker Deployment (Recommended) ✅

**Advantages:**
- One-command startup for all services
- Includes Ollama (no local installation needed)
- Isolated environment, avoids dependency conflicts
- Perfect for production and demos

**Steps:**

```bash
# 1. Ensure Docker Desktop is running
docker ps

# 2. Build and start all services
docker-compose up -d --build

# 3. Wait for services to start (~30 seconds)
sleep 30

# 4. Check service status
docker-compose ps

# Should see three services:
# - magic-academy-backend
# - magic-academy-frontend  
# - magic-academy-ollama ✅
```

#### Option B: Local Development Mode

**Use when:**
- Need to modify code and see changes in real-time
- Don't want to use Docker
- Already have Node.js and Python installed locally

**Steps:**

```bash
# 1. Install Ollama (if not installed)
# macOS:
brew install ollama

# 2. Start Ollama
ollama serve

# 3. Pull models (in another terminal)
ollama pull qwen2.5:7b
ollama pull llama2

# 4. Start backend (from project root)
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev

# Access: http://localhost:5173
```

---

## 🐳 Docker Deployment

### Complete Docker Setup Process

#### 1. First-Time Startup

```bash
# Build all images and start containers
docker-compose up -d --build

# View logs
docker-compose logs -f
```

#### 2. Configure Ollama (Required for First Run)

```bash
# Wait for Ollama container to start (~10-30 seconds)
docker logs -f magic-academy-ollama
# Press Ctrl+C when you see "Ollama is running" or similar

# Pull required models
docker exec magic-academy-ollama ollama pull qwen2.5:7b
docker exec magic-academy-ollama ollama pull llama2

# Verify models are downloaded
docker exec magic-academy-ollama ollama list
# Should see qwen2.5:7b and llama2
```

#### 3. Verify Services

```bash
# Run verification script
./verify-ollama.sh

# Or verify manually
# Test frontend
curl http://localhost

# Test backend API
curl http://localhost:8001/api/game-state

# Test Ollama (via proxy)
curl http://localhost/ollama/api/tags

# Test Ollama (direct access)
curl http://localhost:11434/api/tags
```

### Service Access URLs

After successful startup, you can access:

- **Frontend Application**: http://localhost
- **Backend API**: http://localhost:8001
- **Ollama API (Proxy)**: http://localhost/ollama/api/tags
- **Ollama API (Direct)**: http://localhost:11434/api/tags

### Common Docker Commands

```bash
# View all service status
docker-compose ps

# View logs
docker-compose logs -f              # All services
docker-compose logs -f backend     # Backend only
docker-compose logs -f frontend    # Frontend only
docker-compose logs -f ollama      # Ollama only

# Restart services
docker-compose restart              # All services
docker-compose restart backend     # Backend only

# Stop services
docker-compose stop

# Stop and remove containers (data preserved)
docker-compose down

# Stop and remove containers and volumes (clears all data)
docker-compose down -v

# Rebuild
docker-compose build --no-cache
docker-compose up -d
```

---

## 🔧 Jenkins CI/CD (Optional)

### Why Use Jenkins?

Jenkins enables:
- Automatic build and deployment
- Automatic testing after code push
- Automatic Docker image updates

### Setting Up Jenkins

#### 1. Start Jenkins Container

```bash
# Create Jenkins container
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v jenkins_home:/var/jenkins_home \
  jenkins/jenkins:lts

# Wait for Jenkins to start (~1-2 minutes)
docker logs -f jenkins
# Press Ctrl+C when you see "Jenkins is fully up and running"

# Get initial admin password
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

#### 2. Configure Jenkins

1. **Access Jenkins**
   ```
   http://localhost:8080
   ```

2. **Initial Setup**
   - Paste the password from the command above
   - Select "Install suggested plugins"
   - Create admin account

3. **Install Required Plugins**
   - Manage Jenkins → Manage Plugins
   - Install:
     - ✅ Docker Pipeline
     - ✅ Docker
     - ✅ Git
     - ✅ Blue Ocean (optional, but recommended)

4. **Create Pipeline Job**
   - New Item → Pipeline
   - Job name: `magic-academy-pipeline`
   - Pipeline section:
     - Definition: Pipeline script from SCM
     - SCM: Git
     - Repository URL: `<your Git repository URL>`
     - Script Path: `Jenkinsfile`
   - Save

5. **Run Pipeline**
   - Click "Build Now"
   - View build progress and logs

#### 3. View CI/CD Status

**Method 1: Jenkins Classic UI**
```
http://localhost:8080
```

**Method 2: Blue Ocean (Recommended)**
```
http://localhost:8080/blue
```

### Jenkins Common Operations

```bash
# View Jenkins logs
docker logs -f jenkins

# Restart Jenkins
docker restart jenkins

# Stop Jenkins
docker stop jenkins

# Start Jenkins
docker start jenkins
```

---

## 🔍 Troubleshooting

### Issue 1: Docker Cannot Start Containers

**Symptoms:**
```
docker: request returned 500 Internal Server Error
```

**Solution:**

```bash
# 1. Check if Docker Desktop is running
# Open Docker Desktop app and wait for it to fully start

# 2. Verify Docker works
docker ps

# 3. Restart Docker Desktop
osascript -e 'quit app "Docker"'
sleep 5
open -a Docker
sleep 20

# 4. Try again
docker-compose up -d
```

### Issue 2: Ollama Container Won't Start

**Symptoms:**
- `magic-academy-ollama` not visible in `docker ps`
- Container keeps restarting

**Solution:**

```bash
# View Ollama logs
docker logs magic-academy-ollama

# Check resource usage (may need more memory)
docker stats magic-academy-ollama

# Restart Ollama
docker-compose restart ollama

# If still not working, remove and recreate
docker-compose stop ollama
docker-compose rm ollama
docker-compose up -d ollama
```

### Issue 3: Model Download Fails

**Symptoms:**
```
Error: failed to pull model
```

**Solution:**

```bash
# 1. Check network connection
docker exec magic-academy-ollama ping -c 3 8.8.8.8

# 2. Check disk space
docker system df

# 3. Manually pull with verbose output
docker exec -it magic-academy-ollama ollama pull qwen2.5:7b --verbose

# 4. If disk space insufficient, clean Docker
docker system prune -a
```

### Issue 4: Frontend Cannot Access Backend

**Symptoms:**
- Browser console shows network errors
- API requests fail

**Solution:**

```bash
# 1. Check if backend is running
docker ps | grep backend

# 2. Test backend API
curl http://localhost:8001/api/game-state

# 3. View backend logs
docker logs magic-academy-backend

# 4. Restart backend
docker-compose restart backend
```

### Issue 5: LLM Features Not Working

**Symptoms:**
- Cannot generate knowledge points
- Cannot answer questions
- Shows "LLM service not available"

**Solution:**

```bash
# 1. Verify Ollama is running
docker ps | grep ollama

# 2. Test Ollama API
curl http://localhost/ollama/api/tags

# 3. Check if models are downloaded
docker exec magic-academy-ollama ollama list

# 4. If no models, pull again
docker exec magic-academy-ollama ollama pull qwen2.5:7b

# 5. View Ollama logs
docker logs magic-academy-ollama | tail -50
```

### Issue 6: Port Already in Use

**Symptoms:**
```
Error: bind: address already in use
```

**Solution:**

```bash
# Find process using port
lsof -i :8001   # Backend port
lsof -i :80     # Frontend port
lsof -i :11434  # Ollama port
lsof -i :8080   # Jenkins port

# Kill process (replace <PID> with actual process ID)
kill -9 <PID>

# Or modify docker-compose.yml to use different ports
```

### Issue 7: Frontend Build Fails

**Symptoms:**
```
npm run build fails
TypeScript errors
```

**Solution:**

```bash
# 1. Clear build cache
docker-compose build --no-cache frontend

# 2. Check dependencies
cd frontend
npm ci

# 3. Check TypeScript
npm run type-check
```

---

## 📦 Data Persistence

### Important Data Locations

The following data is persisted:

- **Uploaded files**: `./backend/uploads/`
- **Generated courses**: `./backend/courses/`
- **Ollama models**: Docker volume `ollama_data`
- **Jenkins configuration**: Docker volume `jenkins_home`

### Backup Data

```bash
# Backup uploaded files and courses
tar czf backup-$(date +%Y%m%d).tar.gz backend/uploads backend/courses

# Backup Ollama models
docker run --rm \
  -v ollama_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/ollama-backup.tar.gz /data

# Backup Jenkins
docker run --rm \
  -v jenkins_home:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/jenkins-backup.tar.gz /data
```

### Restore Data

```bash
# Restore uploaded files and courses
tar xzf backup-YYYYMMDD.tar.gz

# Restore Ollama models
docker run --rm \
  -v ollama_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/ollama-backup.tar.gz -C /data
```

---

## 🔄 Updating Code

### Update from Git

```bash
# 1. Pull latest code
git pull origin main  # or master

# 2. Rebuild Docker images
docker-compose build

# 3. Restart services (no need to stop)
docker-compose up -d

# Or completely rebuild (if major changes)
docker-compose down
docker-compose up -d --build
```

### Push Code to Git

```bash
# 1. Check changes
git status

# 2. Add changes
git add .

# 3. Commit
git commit -m "Describe your changes"

# 4. Push
git push origin main  # or master
```

---

## ✅ Verification Checklist

After initial setup, confirm the following:

### Docker Deployment

- [ ] Docker Desktop is running
- [ ] All three containers running (backend, frontend, ollama)
- [ ] Frontend accessible: http://localhost
- [ ] Backend API responds: `curl http://localhost:8001/api/game-state`
- [ ] Ollama API responds: `curl http://localhost/ollama/api/tags`
- [ ] Models downloaded: `docker exec magic-academy-ollama ollama list`

### Functionality Verification

- [ ] Can upload course files
- [ ] Can generate knowledge points
- [ ] LLM can answer questions
- [ ] Can start learning area
- [ ] Can start test (magic duel)

### Jenkins (Optional)

- [ ] Jenkins container running
- [ ] Accessible: http://localhost:8080
- [ ] Pipeline job created
- [ ] Can successfully run build

---

## 📚 Related Documentation

- [README.md](./README.md) - Project overview
- [OLLAMA_DOCKER_SETUP.md](./OLLAMA_DOCKER_SETUP.md) - Detailed Ollama setup guide
- [DEPLOYMENT.md](./DEPLOYMENT.md) - Detailed deployment documentation
- [DEPLOYMENT_QUICK_START.md](./DEPLOYMENT_QUICK_START.md) - Quick deployment reference

---

## 💡 Tips

### Development Mode vs Production Mode

- **Development Mode**: Need to rebuild images after code changes
  ```bash
  docker-compose build frontend
  docker-compose up -d frontend
  ```

- **Production Mode**: Use Docker Compose to manage all services, suitable for stable operation

### Performance Optimization

- Ollama models are large (several GB), be patient on first download
- Ensure Docker Desktop has enough memory allocated (recommend at least 4GB)
- Using SSD can speed up model loading

### Security Recommendations

- Configure HTTPS for production
- Don't commit sensitive information (API keys) to Git
- Use environment variables for configuration

---

## 🆘 Getting Help

If you encounter problems:

1. Check relevant logs: `docker-compose logs -f [service-name]`
2. Run verification script: `./verify-ollama.sh`
3. Check detailed documentation: `OLLAMA_DOCKER_SETUP.md`
4. Check GitHub Issues (if available)

---

## 🎉 Getting Started

After setup is complete, visit **http://localhost** to start using Magic Academy!

Happy learning! ✨

