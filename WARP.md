# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

This is ELEC5620 Group 112's educational game project - a gamified learning platform called "Computer Magic Academy". The application combines game mechanics with educational content delivery, featuring:

- **Game-based Learning**: Students progress through a linear map by completing knowledge-based challenges
- **Teacher Portal**: Educators can upload course materials (PDF/TXT/Markdown) to generate game content
- **AI-powered Content Generation**: Uses Ollama LLM (qwen2.5 model) to parse course materials and generate quizzes
- **Battle System**: Students answer quiz questions in an RPG-style battle interface

## Architecture

### Full-Stack Structure
- **Backend**: Python Flask REST API (port 8001)
- **Frontend**: React + TypeScript + Vite (port 5173)
- **AI Integration**: Ollama for content generation (port 11434, optional)

### Key Components

**Backend (`backend/app.py`)**:
- Flask server with CORS enabled for cross-origin requests
- Game state management (stores in-memory, no database)
- File upload handling (PDF/TXT/Markdown parsing)
- Course generation from uploaded materials (LLM-based or fallback algorithm)
- Quiz generation endpoint for battle system
- Linear map progression system

**Frontend (`frontend/src/`)**:
- `App.tsx`: Main entry point, handles mode switching (student/teacher)
- `GameMap.tsx`: Displays the linear progression map with castle/area nodes
- `AreaView.tsx`: Individual learning area with knowledge points
- `AreaDialog.tsx`: Dialog for area interactions and quiz battles
- `BattleScene.tsx`: RPG-style quiz battle interface with HP bars
- `TeacherPortal.tsx`: Course upload and management interface
- `config/courseMaterials.ts`: Default/fallback course content
- `config/apiKeys.ts`: API configuration (check before using external services)

### Data Flow
1. Teacher uploads course material → Backend parses with Ollama (or fallback) → Generates structured course data
2. Course applied to map → Creates sequential area nodes with knowledge points
3. Student selects area → Views knowledge points → Triggers battle quiz
4. Quiz completion → Updates learning progress → Unlocks next area

### Game State Structure
```javascript
{
  areas: {
    'start': { completed, position, connections, level, castle_type, learningProgress, learnedPoints },
    'area1': { ... },
    // Linear progression: start → area1 → area2 → ...
  },
  current_area: string,
  max_level: number
}
```

### Course Library Structure
```javascript
{
  'area_id': {
    subject: string,
    materials: string[],  // Knowledge points
    difficulty: 'easy' | 'medium' | 'hard',
    category: string,
    knowledgePointCount: number,
    chapter: string,
    parent_course: string
  }
}
```

## Development Commands

### Backend Setup & Running

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run the Flask server
python3 app.py
# Server will start on http://127.0.0.1:8001
```

**Backend Dependencies:**
- Flask 3.1.2 (web framework)
- flask-cors 6.0.1 (CORS support)
- PyPDF2 3.0.1 (PDF parsing)
- requests 2.31.0 (HTTP library for Ollama integration)

### Frontend Setup & Running

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies (first time only)
npm install

# Run development server
npm run dev
# Frontend will start on http://localhost:5173

# Build for production
npm run build
# TypeScript compilation runs first (tsc -b), then Vite build
# Output goes to frontend/dist/

# Preview production build
npm run preview

# Lint code
npm run lint
```

**Frontend Tech Stack:**
- React 19.1.1
- TypeScript 5.8.3
- Vite 7.1.2 (build tool)
- Emotion (@emotion/react, @emotion/styled) for CSS-in-JS
- Framer Motion 12.23.12 (animations)
- Axios 1.11.0 (HTTP client)
- ESLint with React plugins

### Running Both Services

```bash
# Terminal 1 - Backend
cd backend && source venv/bin/activate && python3 app.py

# Terminal 2 - Frontend  
cd frontend && npm run dev
```

### Optional: Ollama Setup

```bash
# Install Ollama from https://ollama.ai

# Pull the qwen2.5 model (used by backend)
ollama pull qwen2.5

# Start Ollama service (usually runs automatically)
# ollama serve  # if not running

# Test Ollama connectivity (from project root)
node test_ollama.js
# Note: test_ollama.js uses 'mistral' model, not qwen2.5
```

**Important:** The backend uses `qwen2.5` model (line 408 in app.py), but `test_ollama.js` uses `mistral` model. To test with the same model as the backend:

```bash
# Pull mistral if you want to run test_ollama.js
ollama pull mistral

# Or modify test_ollama.js to use qwen2.5 model
```

### Monitoring & Debugging

```bash
# Watch backend logs in real-time
cd backend && ./watch_logs.sh

# Or manually
cd backend && tail -f server.log
```

### TypeScript Type Checking

The frontend uses TypeScript with project references configured in `tsconfig.json`. To run type checking:

```bash
cd frontend

# Type check without emitting files
npx tsc -b --noEmit

# Or let the build command handle it (runs tsc -b automatically)
npm run build
```

**Note:** There is no separate `typecheck` script. Type checking happens during the build process.

## Important File Locations

### Backend
- **Entry point**: `backend/app.py` (line 1053-1055 has `__main__` block)
- **Game state**: In-memory global variable in `app.py` (not persisted)
- **Course storage**: `backend/courses/*.json` (generated courses from teacher uploads)
- **Uploads**: `backend/uploads/` (uploaded course materials: PDF/TXT/Markdown)
- **Backend logs**: `backend/server.log`
- **Virtual environment**: `backend/venv/` (should not be committed)
- **Watch script**: `backend/watch_logs.sh` (monitors server.log)

### Frontend
- **Entry point**: `frontend/src/main.tsx`
- **Main app**: `frontend/src/App.tsx` (mode switching, API calls)
- **Components**: `frontend/src/components/`
  - `GameMap.tsx` - Interactive map visualization
  - `AreaView.tsx` - Individual area detail view
  - `AreaDialog.tsx` - Quiz battle interface wrapper
  - `BattleScene.tsx` - RPG battle UI with HP bars
  - `TeacherPortal.tsx` - Course upload and management
- **Config**: `frontend/src/config/`
  - `courseMaterials.ts` - Default/fallback course content
  - `apiKeys.ts` - API configuration (currently unused)
- **Assets**: `frontend/src/assets/` (sprites, images)
- **Build output**: `frontend/dist/` (generated by `npm run build`)

## API Endpoints

Base URL: `http://127.0.0.1:8001/api`

- `GET /` - Health check
- `GET /api/game-state` - Get current game state
- `POST /api/complete-area/<area_id>` - Mark area as completed
- `POST /api/update-learning-progress/<area_id>` - Update knowledge points progress
- `POST /api/upload-course` - Upload course material file
- `GET /api/get-courses` - List all generated courses
- `POST /api/apply-course/<course_id>` - Apply course to game map
- `GET /api/course-library/<area_id>` - Get course materials for an area
- `POST /api/generate-quiz/<area_id>` - Generate quiz questions for battle

## Key Configuration

### Backend Port
- Configured in `app.py` line 1055: `app.run(host='0.0.0.0', port=8001, debug=True)`
- Frontend expects backend on port 8001 (see `frontend/src/App.tsx` line 20-21)

### Frontend Port
- Configured in `frontend/vite.config.ts`: `server.port: 5173`
- Vite proxy configured to forward `/api` requests to `http://127.0.0.1:8000` (note: this conflicts with actual backend port 8001)

**Important:** The Vite proxy targets port 8000, but the backend runs on port 8001. The frontend directly calls `http://127.0.0.1:8001/api` instead of using the proxy (see `App.tsx` lines 20-21).

### CORS
- Backend allows all origins: `CORS(app, resources={r"/*": {"origins": "*"}})`
- CORS must be enabled for direct frontend→backend communication

### Ollama Configuration
- Model: `qwen2.5` (line 408 in app.py)
- Endpoint: `http://localhost:11434/api/generate`
- Falls back to rule-based extraction if Ollama unavailable

## Supported File Formats

The teacher portal accepts:
- **PDF**: Parsed with PyPDF2
- **TXT**: Plain text with optional structured format
- **Markdown (.md)**: Treated like TXT

### Structured TXT Format
Teachers can use a structured format for better parsing:

```
# Course Meta Information
Course Name: Example Course
Category: Computer Science
Difficulty: medium
Description: Course description

# Course Content
## Chapter 1 Name
### Knowledge Point 1
Details about point 1...

### Knowledge Point 2
Details about point 2...
```

Both English and Chinese headers are supported.

## Important Development Notes

### Game State Persistence
- Game state is stored **in-memory only**
- Restarting the backend server resets all progress
- No database is currently implemented
- For persistent storage, consider adding SQLite or PostgreSQL

### LLM Integration
- Ollama is **optional** - system works without it
- Backend has fallback algorithm for content extraction if LLM unavailable
- Test LLM connectivity with `node test_ollama.js` (uses Mistral model example)

### Frontend-Backend Communication
- Frontend directly calls backend API (no API gateway)
- All API calls use axios
- Error handling shows connection status in UI

### Linear Map System
- Areas form a single linear progression path
- Each area connects only to the next area
- No branching paths (unlike earlier versions that had 2-3 branches)
- Position calculation: horizontal layout with fixed 600px spacing

### Asset Requirements
- Castle sprites: 5 types (`/castles/castle1.png` through `/castle5.png`)
- Character sprites: Wizard professor and student with various animations (breathing-idle, fireball, taking-punch)
- Background image: `/game-background.png`

### TypeScript & Linting
- TypeScript strict mode enabled
- ESLint configured with React-specific rules via `eslint.config.js`
- Project uses TypeScript project references (see `tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`)
- No tests currently configured (no Jest, Vitest, or pytest setup)

## Common Development Tasks

### Adding New Knowledge Points
1. Edit `frontend/src/config/courseMaterials.ts` for defaults
2. Or upload new course material via Teacher Portal

### Modifying Game Difficulty
- Quiz generation in `backend/app.py` around line 700-900
- Adjust Ollama prompt for difficulty tuning
- Modify fallback question generation logic

### Changing Map Layout
- Position calculation: `calculate_new_position()` function in `app.py` (line 47-78)
- Adjust `forward_distance` (currently 600px) and `spread` (150px) for spacing

### Adjusting Battle Mechanics
- HP calculation in `BattleScene.tsx`
- Damage values for correct/incorrect answers
- Animation timings and effects

### Course Material Parsing
- Main parsing: `generate_course_from_text()` in `app.py` (line 292-441)
- Structured format: `parse_structured_txt()` (line 231-289)
- Fallback extraction: `generate_course_fallback()` (line 443-650)
