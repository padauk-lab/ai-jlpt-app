# Progress Report No. 01 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 9 to Oct 12, 2026 | 2026-10-12 | HP (Backend and Infrastructure) |

Note: this report said the app covers N1 and N2. That was corrected in Report No. 02: **the app is N1 only**.

## Summary

The team workspace is set up and the backend foundation is built.
The backend runs with one command (`docker compose up`) and answers on `/health`.
This work was in pull request #1, waiting for review.

## Completed

| No. | Task | Owner | Status |
|---|---|---|---|
| 1 | GitHub organization (padauk-lab), team (core) and repository | HP | Done |
| 2 | Branch protection on main (pull request and 1 approval required) | HP | Done |
| 3 | Starter folders, README.md, CONTRIBUTING.md, .gitignore, .env.example | HP | Done |
| 4 | Docker Desktop installed and tested | HP | Done |
| 5 | FastAPI backend with `GET /health` returning `{"status":"ok"}` | HP | In review (pull request #1) |
| 6 | Backend Dockerfile (Python 3.12 slim, non-root user) | HP | In review (pull request #1) |
| 7 | docker-compose.yml (PostgreSQL 16 and backend, with health check) | HP | In review (pull request #1) |
| 8 | Locked Python dependencies (requirements.in and requirements.txt) | HP | In review (pull request #1) |
| 9 | Team roles document and project brief | HP | Done |

## How to run the app

1. Install Docker Desktop, and turn on WSL integration if you use WSL
2. `git checkout main` and `git pull`
3. `cp .env.example .env`, then set your own `POSTGRES_PASSWORD` (also inside `DATABASE_URL`)
4. `docker compose up --build`
5. Open http://localhost:8000/health and http://localhost:8000/docs
6. Stop with Ctrl+C, then `docker compose down`

## Next tasks (Week 1, Oct 12 to 18)

| No. | Task | Owner |
|---|---|---|
| 1 | Review and approve pull request #1 | Any teammate |
| 2 | Draft the API contract in docs/ | HP |
| 3 | Design system and screen sketches | LMHP |
| 4 | Expo project setup in frontend/ | LMHP |
| 5 | Choose the word list source and write one complete sample unit | ANK |
| 6 | Plan which words and grammar go into each session and unit | ANK |
| 7 | Compare LLMs on Burmese and Japanese quality and cost | SWYH |
| 8 | Start the explanation script using the sample unit format | SWYH |
