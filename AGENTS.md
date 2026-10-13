# Instructions for AI coding tools

This file is for AI assistants (Claude Code, Copilot, Cursor, ChatGPT and others) working in this repository.
Humans should read it too.

## Project in one paragraph

AI JLPT App by Padauk Lab: a study app for **JLPT N1 only**, for **Burmese speakers**.
Users study 20 sessions (10 units each, 20 words and 1 grammar pattern per unit), take a quiz every 5 units,
and a mock test after each session. AI is used through two buttons only: "More examples" and "Why?".
The app runs on iOS, Android and web.

## Tech stack

- Frontend: Expo (React Native), in `frontend/`
- Backend: FastAPI, Python 3.12, in `backend/`
- Database: PostgreSQL 16
- Local setup: Docker and Docker Compose (`docker compose up --build`)

## Read these first, in this order

1. `docs/project-brief.md`: what we are building
2. `docs/team-roles.md`: who owns what
3. `docs/api-contract.md`: every endpoint and JSON shape. **This is the source of truth.**
4. `docs/progress/`: progress reports. Read the **highest number** for the latest status and next tasks
5. `CONTRIBUTING.md`: team workflow and rules

## Rules for AI assistants

1. **Follow `docs/api-contract.md` exactly.** Use the exact endpoint paths, field names and JSON shapes. Do not invent new endpoints or fields. If something the user asks for is not in the contract, say so and suggest a contract change instead of coding around it.
2. **Stay in the user's own area.** Ask which role the user has (see `docs/team-roles.md`) and only change files in that area unless the user confirms otherwise.
3. **Language:** all explanations, meanings, notes, translations and AI answers shown to users are in **Burmese**. Only the Japanese being learned stays in Japanese. Code, comments and commit messages are in English.
4. **Never commit secrets.** No `.env`, API keys, passwords or tokens in code or commits. Use environment variables. `.env.example` holds fake values only.
5. **Security first:** the backend checks every rule itself and never trusts the app. Passwords are stored only as hashes. Correct answers are never sent to the app before the user answers.
6. **Dependencies:** Python libraries go in `backend/requirements.in`, then `backend/requirements.txt` is regenerated with exact pinned versions. Never add unpinned libraries.
7. **Small changes:** one feature per branch and pull request. Branch names: `feature/...`, `fix/...`, `docs/...`. Never push to `main`.
8. **Explain your code.** The user must be able to explain everything they commit, so explain what you wrote in simple terms.

## How the parts connect

- The app (LMHP) calls the backend API (HP).
- The backend calls AI functions in `backend/app/ai/` (SWYH), which call the LLM service. The app never calls the LLM directly.
- Learning content (words, grammar, proverbs, questions) is prepared by ANK in `data/` and loaded into the database.

## Where to find current status

- Latest progress report: `docs/progress/` (highest number)
- Open tasks: GitHub Issues and the Project board
- Recent work: `git log` and merged pull requests
