# Progress Report No. 02 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 12 to Oct 13, 2026 | 2026-10-13 | HP (Backend and Infrastructure) |

## Summary

The backend foundation is merged into main, and the first full team workflow (branch, pull request, review, merge) is complete.
The API contract is written: 37 endpoints in 4 sections, in pull request #2 for review.
Several product decisions were made, including one correction: **the app is for JLPT N1 only**.

## Completed

| No. | Task | Owner | Status |
|---|---|---|---|
| 1 | Pull request #1 (backend skeleton, Dockerfile, docker-compose) reviewed by LMHP and merged into main | HP, LMHP | Done |
| 2 | 4th member joined Padauk Lab and the core team | HP | Done |
| 3 | Screen flow drafted with reference images: onboarding, dashboard, session, unit, saved words, settings | HP | Done |
| 4 | API contract v0.1 in `docs/api-contract.md` (37 endpoints, 4 sections) | HP | In review (pull request #2) |
| 5 | Project brief, team roles, progress reports and AGENTS.md moved into the repo | HP | In review |

## Key product decisions

| Area | Decision |
|---|---|
| Level | **JLPT N1 only** (corrects earlier documents that said N1 and N2) |
| Language | All explanations, meanings, notes and AI answers in Burmese. Only the Japanese being learned stays Japanese |
| Sign up | Email, username and password, or Google. Stay logged in for weeks. Password at least 8 characters |
| Onboarding | One setup screen: last level (N1, N2, not taken), score (0 to 180), exam date (or not decided, default pace 3 units per day) |
| Units | Unlock in order. Done when the user taps Mark as done. Saved words (bookmarks) included |
| Quiz | Every 5 units, 20 questions, instant feedback, 70% to pass, unlimited retakes, best score counts |
| Mock test | 45 language knowledge questions plus 3 readings (short, medium, long). One continuous strict 30-minute test, no pass mark, resume if the app closes |
| Pass prediction | On the dashboard. Only the first attempt of each mock test counts. Reset all progress in Settings starts a new round |
| AI | Only 2 buttons: More examples (units) and Why? (quiz and mock test review). No chat tab. Explanations saved and reused |
| Dashboard | Progress bar, pass prediction, today's goal, continue button, Proverb of the day, 20 sessions |
| Navigation | Bottom tabs: Home, Saved words, Settings |
| Settings | Profile, study setup, notifications, change password, log out, delete account, reset all progress |

## API contract overview

| Section | Covers | Endpoints |
|---|---|---|
| 1. Onboarding | Login, sign up, Google, password reset, setup, study plan | #1 to #10 |
| 2. Dashboard, sessions and units | Dashboard, proverb, session, unit, mark as done, saved words | #11 to #18 |
| 3. Quiz and mock test | Start, answer, finish, review, resume, submit, result | #19 to #26 |
| 4. AI and settings | More examples, Why?, settings, notifications, devices, account, reset progress | #27 to #37 |

HP builds all endpoints, LMHP calls them from the app. SWYH writes the AI functions that endpoints #27 and #28 call. ANK prepares content in the formats the contract defines.

## What everyone should do now

1. Review your part of pull request #2 and comment on any line you want changed
2. `git pull`, then ask your AI to read `AGENTS.md` and the `docs/` folder
3. Pull main and run the backend once: `docker compose up --build`, then open http://localhost:8000/health

## Next tasks (Week 1, Oct 12 to 18)

| No. | Task | Owner | Depends on |
|---|---|---|---|
| 1 | Review and approve pull request #2 (API contract) | LMHP, SWYH, ANK | Nothing |
| 2 | Database design based on the contract | HP | Task 1 |
| 3 | Placeholder endpoints that return the contract's example JSON | HP | Task 1 |
| 4 | Design system and onboarding and dashboard screens, using the contract's examples as fake data | LMHP | Task 1 |
| 5 | One complete sample unit in the contract format | ANK | Task 1 |
| 6 | First proverb list (effort, consistency, never giving up, not wasting time) | ANK | Nothing |
| 7 | Compare LLMs, then agree with HP on the AI functions for More examples and Why? | SWYH | Task 1 |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test template (ANK to confirm against the N1 format)
3. How last level and score change the daily pace (HP to propose)
4. Which LLM to use (SWYH to propose)
5. Daily limit for More examples, currently 50 (team to decide after testing)
