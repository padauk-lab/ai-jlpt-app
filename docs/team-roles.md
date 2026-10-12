# Team roles

Last updated: 2026-10-13

Each member works independently with fake or sample data, then integrates step by step.
The two agreements everyone builds against are the **API contract** (`docs/api-contract.md`) and the **content format** (inside the contract, sections 2 and 3).

## HP: Backend and Infrastructure

Owns: `backend/` (except `backend/app/ai/`), Docker, GitHub setup.

- GitHub organization, repository, branch protection, Project board
- Docker and docker-compose with the database
- Database tables (until ANK takes them over after Dec 6)
- All API endpoints in the contract: login, onboarding, plan, dashboard, units, quiz, mock test, settings
- Study plan calculation (the numbers are done in code, not by AI)
- Calls SWYH's AI functions from the AI endpoints, and saves "Why?" explanations for reuse
- Later: push notifications, automatic checks (GitHub Actions), cloud deployment

## LMHP: Frontend and Design

Owns: `frontend/`.

- Design system: colors, fonts, spacing, icons, logo
- All screens: splash, login, setup, plan, dashboard, session, unit, saved words, quiz, mock test, settings
- Builds screens with the contract's example JSON as fake data first, then connects to the real backend
- Shows readings above kanji using the contract's `ruby` format
- Tests Burmese and Japanese text on real phones

## ANK: Data and Content

Owns: `data/`.

Until the JLPT on Dec 6, review-focused work only, to protect exam study time.

- Chooses the vocabulary and grammar source list
- Writes one complete sample unit in the contract format
- Plans which words and grammar go into each session and unit
- Proverb list with readings and Burmese meanings
- Mock test template (question split, time setting)
- Reviews AI-drafted content and saved "Why?" explanations
- Tests screens as a real N1 learner
- After Dec 6: takes over the database tables

## SWYH: AI Integration

Owns: `backend/app/ai/`.

- Chooses the LLM service (Burmese quality, Japanese accuracy, cost)
- Writes the AI functions the backend calls:
  - `generate_examples(word_or_grammar)`: 3 new example sentences with Burmese translations
  - `explain_answer(question, selected_option)`: why the correct answer is right and why the selected one is wrong
  - The study plan tip
- AI answers in Burmese as a patient, professional Japanese teacher, with simple examples and analogies
- Scripts that draft content for ANK to review
- Keeps a log of prompts tried and what improved results

## How the parts connect

App (LMHP) → Backend endpoints (HP) → AI functions (SWYH) → LLM service.
Content (ANK) → database → backend endpoints → app.

## Everyone

- Work on your own branch, never push to `main`
- Every pull request needs 1 approval from a teammate
- Never commit `.env`, API keys or passwords
- Stay in your own folder, ask before changing someone else's area
- Using AI is fine, but you must be able to explain everything you commit
