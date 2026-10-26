# Project brief: AI JLPT App

Last updated: 2026-10-13

## What we are building

A study app that helps **Burmese speakers pass the JLPT N1**, with AI that explains answers and a personal study plan.
It runs on **iOS, Android and web** from one codebase.

This is a learning project for Padauk Lab. The goal is real team experience (Git, GitHub, Docker, code review),
built with production practices.

## Users and languages

- Target: JLPT **N1 only**
- App text: **Burmese and Japanese only**
- All explanations are in Burmese. Only the Japanese being learned stays in Japanese.

## How the app works, in the order a user meets it

1. **Splash and login**: email, username and password. Users stay logged in for weeks. "Forgot password" sends a 6-digit code by email. (Google login comes later, together with Sign in with Apple.)
2. **First-time setup** (one screen, shown once): last JLPT level taken (N1, N2, not taken), score (0 to 180), and exam date (or "not decided yet").
3. **Study plan**: the backend calculates units per day until the exam. The AI adds a short tip.
4. **Dashboard**: overall progress, pass prediction, today's goal, continue button, Proverb of the day, and 10 sessions.
5. **Sessions and units**: 10 sessions, 10 units each (2,000 core N1 words). Each unit has 20 words and 1 grammar pattern, each with Burmese meaning, readings above kanji, and 2 to 3 example sentences. Units unlock in order. A unit is done when the user taps "Mark as done".
6. **Quiz**: every 5 units. 20 questions, instant green or red feedback, 70% to pass, unlimited retakes.
7. **Mock test**: after each session. 45 language knowledge questions plus 3 readings (short, medium, long). One continuous strict 30-minute test. No pass mark. Only the first attempt counts toward the pass prediction.
8. **Saved words**: users bookmark words to review later.
9. **AI help**: two buttons only. "More examples" on word and grammar cards, and "Why?" in quiz and mock test review. No chat.
10. **Settings**: profile, study setup, notifications, password, log out, delete account, reset all progress.
11. **Notifications**: daily study reminder and Proverb of the day (theme: effort, consistency, not giving up, not wasting time).

Bottom tabs: Home, Saved words, Settings.

## Tech stack

| Part | Tool |
|---|---|
| Frontend | Expo (React Native) |
| Backend | FastAPI, Python 3.12 |
| Database | PostgreSQL 16 |
| Local setup | Docker and Docker Compose |
| AI | An LLM service called only from the backend (to be chosen) |

## Key documents

- `docs/api-contract.md`: every endpoint and JSON shape
- `docs/team-roles.md`: who owns what
- `docs/progress/`: progress reports
