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
   (Already have a .env? Compare it with .env.example and add any new lines. For the web app you need `CORS_ORIGINS=http://localhost:8081`)
3. Run `docker compose up --build`
4. Open http://localhost:8000/health, you should see {"status":"ok"}
5. API docs: http://localhost:8000/docs
6. Stop with Ctrl+C, then `docker compose down`

## Testing the app on a real phone (home Wi-Fi only)
1. In your own `.env`, add `BACKEND_HOST=0.0.0.0`, then restart: `docker compose up --build`
2. Find your computer's Wi-Fi address (Mac: System Settings > Wi-Fi > Details, e.g. `192.168.1.23`)
3. In `frontend/.env`, set `EXPO_PUBLIC_API_URL=http://192.168.1.23:8000/api/v1` (your address)
4. Start the app with `npx expo start` and open it with Expo Go on the phone (same Wi-Fi)
5. When done, remove `BACKEND_HOST` again. Never use it on public Wi-Fi.

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
