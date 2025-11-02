# Harry Potter Learning System

## Project Overview
The Harry Potter Learning System is an AI-powered educational game that combines interactive learnin and battle mechanics. Teachers can upload the learning materials and AI will split it into detailed learning point and students can learn step by step and AI tutor will answer their questions in detail. Students engage in "Magic Duels" against AI professors, where each correct answer inflicts damage on the opponent -- AI progessors, and incorrect answers reduce the player's HP. Feedback modeul provides learning reports including correct accuracy, progress tracking, feedback, and status of each knowlege point. Through this gamified approach, students can study, battle, and review their learning progress in an engaging and adaptive environment

## System Design & Objectives
The system aims to enhance learning motivation through gamification and AI-driven adaptive teaching.  
It transforms passive learning into an active, interactive experience.

### Design Objectives
- **Personalized Learning:**
  AI professor adjusts question difficulty dynamically based on student performance.  
- **Gamified Motivation:**
  Learning progress is visualized through duels, progress bars, and unlockable stages.  
- **Continuous Feedback:**
  Real-time results and post-duel summaries help students identify weak areas.  
- **Modular Scalability:**
  Each feature (Teacher Portal, Student Map, Duel) is independently deployable for future extensions.  
- **Efficient AI Integration:**
  Combines local inference and cloud models for flexible, cost-effective performance.

## Configuration

### Environment Requirements
        | Component | Version |
        |------------|----------|
        | Python | >= 3.10 |
        | Node.js | >= 18 |
        | npm | >= 9 |
        | Ollama | Latest (supports Qwen2.5) |

## Deployment
This section explains how to install dependencies and run the project locally, including backend, frontend, and the local AI model
  **Backend**
   - `cd backend`
   - `pip install -r requirements.txt`
   - `python app.py`

  **Frontend**
   - `cd frontend`
   - `npm install`
   - `npm run dev`

  **Local Model**
   - `ollama run qwen2.5`

## Technology and Implementation

The Harry Potter Learning System adopts a full-stack AI-driven architecture integrating React (frontend), Flask (backend), and local LLM inference via Ollama.  
It supports modular feature updates and iterative Agile development for learning, testing, and feedback loops.

### Frontend (React + TypeScript + Vite)
- Built with **React + TypeScript + Vite**, ensuring high performance and modular code reuse.  
- Implements dynamic interfaces for:
  - Student Map (progress tracking, castle unlocking)
  - Magic Duel Scene (battle interaction)
  - Teacher Portal (material upload & preview)
- Communicates with the backend through RESTful APIs for lesson data, duel status, and progress updates.
- Integrates **MathJax** to render mathematical formulas in learning dialogues.

### Backend (Flask)
- Developed using **Flask (Python 3.9)**, handling:
  - Course parsing and conversion to structured JSON
  - AI-powered question generation
  - Game logic management (HP calculation, duel outcomes)
- Stores user progress and course data persistently via JSON and backend cache.

### AI Integration (Ollama + Claude)
- **Ollama (local container)** manages the **Qwen2.5** model for generating learning questions and hints.  
- **Claude 3.5 (cloud API)** serves as a backup and advanced reasoning layer for detailed explanations and error correction.  
- AI response flow:
  1. Teacher uploads course material.
  2. Backend sends parsed content to Ollama/Claude.
  3. Model returns structured JSON with knowledge points and multiple-choice questions.
  4. Frontend renders these in the Magic Duel interface.

### Deployment & Infrastructure
- **Docker + Docker Compose** containerize all services (frontend, backend, Ollama) for reproducible environments.  
- **Nginx** acts as a reverse proxy, managing `/api` and `/ollama` routes.  
- Cloud hosting via **Render (backend)** and **Vercel (frontend)** for free-tier deployment.  

### CI/CD & Development
- **Jenkins + Jenkinsfile** automate build, test, and deployment workflows.  
- **GitHub** serves as version control and collaboration hub.  
- **ESLint** enforces frontend code quality, ensuring maintainable React components.

### Creative & AI Tools
- **Pixellab** for pixel-style character design and animations.  
- **ChatGPT / Sora** for background scene generation and storytelling enhancement.  
- **Cursor & Claude** assisted debugging and AI prompt engineering.


## Data Flow & System Architecture
1. Teacher uploads course material (TXT/PDF/MD) via the Teacher Portal.
2. Flask backend parses and extracts key learning points.
3. Ollama engine (Qwen2.5) generates structured question data.
4. Frontend React displays learning dialogues, maps, and duel scenes.
5. Student performance and HP status are synchronized with backend APIs.
6. The Feedback Module analyzes performance and generates summary reports.
- This modular data flow enables both local and cloud-based AI learning environments.

## Visualization and Reporting
- **Dynamic Result Visualization:**  
  The frontend uses React-based chart libraries (such as Chart.js / Recharts) to visualize duel outcomes, learning accuracy, and progression over time.  
- **Automated Summary Reports:**  
  The backend aggregates user performance and generates personalized reports summarizing learning achievements, weak points, and recommended improvements.
- **Data Flow Integration:**  
  Real-time progress data is transmitted from the backend to the frontend through RESTful APIs, ensuring synchronized updates during and after each magic duel.
- **Future Extension:**  
  The reporting module can be expanded to include teacher dashboards and class-level analytics for group performance tracking.


## Data Flow & System Architecture
1. Teacher uploads course material (TXT) via the Teacher Portal.
2. Flask backend parses and extracts key learning points.
3. Ollama engine (Qwen2.5) generates structured question data.
4. Frontend React displays learning dialogues, maps, and duel scenes.
5. Student performance and HP status are synchronized with backend APIs.
6. The Feedback Module analyzes performance and generates summary reports.
- This modular data flow enables both local and cloud-based AI learning environments.

## Future Improvements
- To further enhance system scalability and interactivity, the following improvements are planned:
- **Adaptive Difficulty:**
  Introduce reinforcement learning to personalize question difficulty dynamically.
- **Multiplayer Mode:**
  Support peer-vs-peer duels and cooperative learning groups.
- **Voice Interaction:**
  Enable speech recognition for hands-free learning.
- **Database Upgrade:**
  Migrate from JSON storage to a structured SQL/NoSQL system.
- **Teacher Dashboard:**
  Add data analytics for class-level performance monitoring.
- **Accessibility:**
  Implement localization and accessibility support for broader audiences.

## User Stories

### Teacher Side (Course Management)

| ID | Feature |
|----|---------|
| **US-T1** | Upload TXT course materials (≤16 MB) |
| **US-T2** | Automatically extract 10-15 knowledge points from LLM |
| **US-T3** | View, edit, and delete generated courses |
| **US-T4** | Apply courses to the student map (replace/append) |
| **US-T5** | Reset student progress |
| **US-T6** | Save courses for later use |
| **US-T7** | Switch between multiple courses |

### Student Side (Learning & Testing)

| ID | Feature |
|----|---------|
| **US-S1-S2** | Browse / navigate the learning map |
| **US-S4-S5** | Learn knowledge points and interact with AI professors |
| **US-S6-S7** | View learning progress and completed knowledge points |
| **US-S8-S12** | Take Magic Duel tests, get hints, view battle reports, and unlock the next area |
| **US-S13-S14** | View battle reports and final summaries |

---

## Feedback Loop

### Core User Stories (Feedback)

| ID | Feature |
|----|---------|
| **US-FB3** | Get personalized knowledge point review recommendations |
| **US-FB4** | Automatically adjust question difficulty |
| **US-FB9** | Dynamically generate adaptive questions |

### Teacher Dashboard

| ID | Feature |
|----|---------|
| **US-FB6** | View student feedback summary |
| **US-FB7** | Improve courses based on feedback |
| **US-FB12** | Continuously optimize courses |

### AI Self-Improvement

| ID | Feature |
|----|---------|
| **US-FB8** | AI iterates itself based on accumulated feedback |

---

## Iteration Report

### Key Achievements & Challenges per Phase

| Phase | Goal | Achievements | Challenges |
|-------|------|--------------|------------|
| **1** | Basic Infrastructure | React + TS front-end, Flask API, map rendering, character animation | TypeScript config, state management |
| **2** | Teacher Side & Course Generation | File upload, Ollama LLM extraction, TXT parsing, JSON persistence | PDF parsing reliability, prompt engineering |
| **3** | Learning System Enhancement | Dynamic course loading, progress persistence, MathJax rendering | Cross-session persistence, formula performance |
| **4** | Testing System Redesign | Combat UI, LLM question generation, HP mechanics, animations | Question consistency, animation smoothness |
| **5** | Map System Reconstruction | Linear progress, 80% unlock rule, progress bar, character movement | Logic simplification |
| **6** | Deployment & CI/CD | Docker containerization, Compose, Jenkins pipeline, docs | Docker networking, Ollama proxy |

### Technology Stack

| Layer | Tech | Version | Purpose |
|-------|------|---------|---------|
| **Frontend** | React | 19.1.1 | Component UI framework |
| | TypeScript | 5.8.3 | Type safety |
| | Vite | 7.1.2 | Fast build & dev server |
| | Emotion | 11.14.1 | CSS-in-JS |
| | Axios | 1.11.0 | HTTP client |
| | MathJax | 3.x (CDN) | Formula rendering |
| **Backend** | Flask | 3.1.2 | REST API |
| | Flask-CORS | 6.0.1 | CORS handling |
| | PyPDF2 | 3.0.1 | PDF extraction |
| | Requests | 2.31.0 | LLM API calls |
| **Infrastructure** | Docker | - | Containerization |
| | Docker-Compose | - | Orchestration |
| | Nginx | - | Reverse proxy |
| | Ollama | - | Local LLM service |
| | Jenkins | - | CI/CD pipeline |

## Contribution Table
| Name          | SID        | Contribution (%) |
|----------------|-------------|------------------|
| Qinan Zhou     | 530634247   | 20% |
| Lin Zhao       | 520539392   | 20% |
| Qihan Zhu      | 550489593   | 20% |
| Mingze Li      | 550374130   | 20% |
| Shimin Yuan    | 540269530   | 20% |