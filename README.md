# Magic Academy Learning RPG

An English-first, 16-bit pixel-style learning RPG that connects a Teacher Portal for course generation with a Student Map for exploration and testing. The system integrates LLMs to teach, explain knowledge points, and generate tests. A battle scene turns tests into a magic duel against an AI professor.

> 📖 **Setup Guide**: See [SETUP_GUIDE.md](./SETUP_GUIDE.md) for complete setup instructions after pulling from Git (including all operations from clone to deployment)

## Features

### Teacher Portal
- Upload PDF/TXT/MD course materials (structured TXT supported)
- LLM-based course generation with knowledge points
- Course persistence (save, view, delete, apply to game)
- Apply courses either replacing or adding to the current map
- Unified background with student portal

### Student Map (Linear Progression)
- Start area + linearly unlocked areas (one-by-one progression)
- Horizontal map with scroll; castles as areas
- Learning progress bar above each area
- Test badge to the right of progress bar, center-aligned vertically
- Locked areas show tooltip; desaturated visuals (not opacity)
- Character moves with 4-direction walking GIFs; idle defaults to `wizard_idle.gif`

### Area Dialog (Learning UI)
- Fully English UI and content
- Dynamic course loading from backend
- Persistent learning progress per area
- Math rendering with MathJax for inline `\( ... \)` and block `\[ ... \]` TeX
- Avatars on both sides (student/professor), 3x pixel scale
- "Start Magic Duel" button appears only when ≥20% of knowledge points are learned

### Battle Scene (Magic Duel Testing)
- 16-bit pixel UI with HP bars (80% to pass and unlock next area)
- Card-style options; one round per question
- LLM-generated questions with strict JSON format prompts
- Student/professor sprites 3x scaled; attack (fireball), hit, and shake animations
- Hint button with AI-generated hints, clearly labeled "AI GENERATED"
- Loading screen: pixel progress bar with movable pixel head icon

### LLM Integration
- **Ollama in Docker**: Runs in Docker container with persistent model storage
- Local models via Ollama (e.g., `qwen2.5:7b`, `llama2`)
- Optional online model (Claude 3.5) through backend relay
- Frontend access via Nginx proxy (`/ollama`), backend via Docker network
- Prompting optimized to use ONLY course content and output English
- Question generation suppresses thinking display and shows progress

## Repository Structure

```
backend/
  app.py                 # Flask server, course processing, game state APIs
  Dockerfile             # Backend container definition
  requirements.txt       # Python dependencies
  uploads/              # Uploaded source files (PDF/TXT/MD)
  courses/               # Generated course JSON files

frontend/
  public/
    castles/             # castle{1..N}.png area images
    character/           # Sprite GIFs (idle/walk/attack/hit)
    roads/               # path.png (map road image)
    ui/                  # duel-head.png (progress icon)
  src/components/
    App.tsx              # Mode switching, root routing
    TeacherPortal.tsx    # Upload, generate, persist courses
    GameMap.tsx          # Map rendering, areas, progress, badges
    AreaDialog.tsx       # Learning, chat, math rendering, avatars
    BattleScene.tsx      # Pixel duel UI, HP, options, animations
  src/config/
    apiConfig.ts         # Centralized API URL configuration
    apiKeys.ts           # API key placeholders
  Dockerfile             # Frontend container definition
  nginx.conf             # Nginx configuration for production

docker-compose.yml       # Multi-container orchestration
Jenkinsfile              # CI/CD pipeline definition
DEPLOYMENT.md            # Detailed deployment guide
DEPLOYMENT_QUICK_START.md # Quick deployment reference
```

## Prerequisites

### For Development
- Node.js 18+
- Python 3.9+
- Ollama (optional, if running locally) with at least `qwen2.5:7b` pulled

### For Docker Deployment
- Docker & Docker Compose
- **Ollama runs in Docker** - no local installation needed! 🎉

## Quick Start (Development)

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Backend runs on `http://127.0.0.1:8001`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend dev server runs on `http://localhost:5173`

## Docker Deployment

### Quick Start

```bash
# Build and start all services (including Ollama)
docker-compose up -d --build

# Pull required Ollama models (first time only)
docker exec magic-academy-ollama ollama pull qwen2.5:7b
docker exec magic-academy-ollama ollama pull llama2

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Access:**
- Frontend: http://localhost
- Backend API: http://localhost:8001
- Ollama API: http://localhost:11434 (or via `/ollama` proxy)

**See [OLLAMA_DOCKER_SETUP.md](./OLLAMA_DOCKER_SETUP.md) for detailed Ollama setup.**

See `DEPLOYMENT_QUICK_START.md` for detailed deployment instructions.

## Jenkins CI/CD

### Setup

1. Install Jenkins plugins:
   - Docker Pipeline
   - Docker
   - Git

2. Create Pipeline job:
   - **New Item** → **Pipeline**
   - **Definition**: Pipeline script from SCM
   - **SCM**: Git
   - **Repository URL**: Your repo URL
   - **Script Path**: `Jenkinsfile`

3. Configure environment variables (optional):
   - `DOCKER_REGISTRY`: Your Docker registry URL

### Pipeline Stages

1. **Checkout**: Clone repository
2. **Build Backend**: Build Docker image
3. **Build Frontend**: Build Docker image
4. **Test**: Verify builds
5. **Deploy**: Deploy using docker-compose (main/master branch only)

See `DEPLOYMENT.md` for comprehensive deployment guide.

## Environment Configuration

### Development

Frontend uses hardcoded URLs for development. For production:

Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8001/api
VITE_OLLAMA_URL=http://127.0.0.1:11434
```

### Production (Docker)

Set via `docker-compose.yml` build args:
```yaml
args:
  - VITE_API_BASE_URL=http://localhost:8001/api
```

Or use environment variables in `docker-compose.yml` for runtime configuration.

## Math Rendering

MathJax v3 is loaded automatically. Supported delimiters:

- Inline: `\( v = u + at \)` or `$v = u + at$`
- Display: `\[ s = ut + \tfrac{1}{2}at^2 \]` or `$$ s = ut + \tfrac{1}{2}at^2 $$`

## Structured TXT Format

Teachers can upload structured TXT files:

```
# Course Meta Information
Course Name: Physics Fundamentals
Category: Science
Difficulty: medium

# Course Content
- Kinematics: ...
- Newton's Laws: ...
```

Backend supports English headers and automatically extracts knowledge points.

## Troubleshooting

### Backend port in use
```bash
lsof -ti:8001 | xargs kill -9  # macOS/Linux
```

### Ollama not responding

**Docker Deployment:**
```bash
# Check Ollama container
docker ps | grep ollama

# View Ollama logs
docker logs magic-academy-ollama

# Pull models in Docker
docker exec magic-academy-ollama ollama pull qwen2.5:7b

# Test Ollama API
curl http://localhost/ollama/api/tags  # Via proxy
curl http://localhost:11434/api/tags  # Direct
```

**Local Development:**
- Ensure Ollama is running: `ollama serve`
- Check models: `curl http://127.0.0.1:11434/api/tags`
- Pull missing models: `ollama pull qwen2.5:7b`

### Docker issues
- Clear cache: `docker-compose build --no-cache`
- View logs: `docker-compose logs -f [service_name]`

### API connection errors
- Verify backend is running: `curl http://localhost:8001/api/game-state`
- Check `VITE_API_BASE_URL` matches your backend URL
- For Docker, ensure services are on the same network

## Security Notes

- API keys should be injected via environment variables for production
- This demo uses a development Flask server; use a production WSGI server (gunicorn/uwsgi) for production
- Configure HTTPS via reverse proxy (nginx/traefik)
- Restrict backend port (8001) to internal network in production

## License

For course/demo use. Replace assets and configure licenses appropriately for your deployment.
