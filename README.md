# AI JLPT App

A GenAI JLPT study app for Burmese speakers, built by Padauk Lab.

## Features
- Google login and first-time setup (level, score, exam date)
- 20 sessions, 10 units each, 20 words and 1 grammar pattern per unit
- Quizzes every 5 units and a mock test after each session
- AI explanations, an Ask AI chatbot, and a personalized study plan
- Burmese and Japanese interface

## Tech stack
- Frontend: Expo (React Native), iOS, Android and web
- Backend: FastAPI (Python)
- Database: PostgreSQL
- Docker and Docker Compose

## Project structure
- frontend/  screens and UI
- backend/   API, login, study plan, AI integration
- data/      vocabulary, grammar, proverbs, mock test templates
- docs/      API contract and diagrams

## Getting started
1. Clone the repo
2. Copy .env.example to .env and fill in the values
3. Run `docker compose up --build`
4. Open http://localhost:8000/health, you should see {"status":"ok"}
5. API docs: http://localhost:8000/docs
6. Stop with Ctrl+C, then `docker compose down`

## Team
- HP: Backend and Infrastructure
- LMHP: Frontend and Design
- ANK: Data and Content
- SWYH: AI Integration

Read CONTRIBUTING.md before you start.

## Documentation
- [AGENTS.md](AGENTS.md): instructions for AI assistants, read this first
- [Project brief](docs/project-brief.md)
- [Team roles](docs/team-roles.md)
- [API contract](docs/api-contract.md)
- [Progress reports](docs/progress/) (PDF versions in [docs/pdf](docs/pdf/))
