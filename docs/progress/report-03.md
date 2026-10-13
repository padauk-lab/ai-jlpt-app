# Progress Report No. 03 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 13, 2026 | 2026-10-13 | HP (Backend and Infrastructure) |

## Summary

The API contract is merged into main.
The database is designed and built: **27 tables in 5 groups**, written as Python models, with the first migration.
All 27 tables were created and checked in PostgreSQL in Docker.
The design (pull request #4) and the code (pull request #5) are waiting for review.

## Completed

| No. | Task | Owner | Status |
|---|---|---|---|
| 1 | API contract (pull request #2) reviewed and merged into main | HP, team | Done |
| 2 | Database design v0.1 in `docs/database-design.md` (27 tables, 5 groups) | HP | In review (pull request #4) |
| 3 | New libraries added and pinned: SQLAlchemy, Alembic, psycopg | HP | In review (pull request #5) |
| 4 | Database connection (`backend/app/db.py`), reads `DATABASE_URL` from `.env` | HP | In review (pull request #5) |
| 5 | Python models for all 27 tables (`backend/app/models/`) | HP | In review (pull request #5) |
| 6 | Alembic set up, and the first migration that creates every table | HP | In review (pull request #5) |
| 7 | Tested in Docker: 27 tables created, code and database match | HP | Done |

## The database at a glance

| Group | Tables | What it stores |
|---|---|---|
| 1. Users and login | 5 | Accounts, login tokens, password reset links, devices, notification settings |
| 2. Study setup and plan | 3 | Setup answers, study plan, official exam dates |
| 3. Learning content | 6 | Sessions, units, words, grammar, example sentences, proverbs |
| 4. Quizzes and mock tests | 4 | Quizzes, mock tests, reading passages, questions |
| 5. Progress and AI | 9 | Units done, saved words, quiz and mock test attempts and answers, saved "Why?" explanations, AI usage |

Key ideas:

- **Reset all progress** adds 1 to the user's round. Nothing is deleted, so old rounds stay as history.
- **Calculated, not stored**: days left, progress, best score and pass prediction are worked out when needed, so they are never out of date.
- **Google login** uses Google's permanent user ID (`google_sub`) in the users table. No extra table is needed.
- **Furigana** is stored twice: as plain text for search (`furigana`) and in the contract's `ruby` format for display.

## Safety rules inside the database

The database itself refuses bad data, even if the code has a bug. Examples:

| Rule | What it blocks |
|---|---|
| An account needs a password or a Google ID | Accounts nobody can log in to |
| Emails are stored lowercase | Two accounts for `Htet@x.com` and `htet@x.com` |
| No score when the last level is "not taken" | Impossible setup answers |
| Only one mock test in progress per user and test | Two open tests at once (retakes after submitting are allowed) |
| Every question has exactly 4 options, answer `a` to `d` | Broken questions |
| One answer per question per quiz attempt | Answering twice |
| Deleting a user deletes their data | Personal data left behind |
| Content can't be deleted while something uses it | Losing words or questions by accident |

Passwords and tokens are stored only as hashes. Correct answers are never sent to the app before the user answers.

## How to get the database on your computer

After pull request #5 is merged:

1. `git checkout main` and `git pull`
2. `docker compose run --rm --build backend alembic upgrade head`
3. Check: `docker compose exec db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"'` shows 28 rows (27 tables plus `alembic_version`)

The database starts empty. Content from ANK is loaded in later.

## What everyone should do now

1. Review pull requests #3, #4 and #5. One approval each is enough
2. In pull request #4, check your part:
   - ANK: Groups 3 and 4 (content and questions)
   - SWYH: `ai_explanations` and `ai_usage`
   - LMHP: anything that does not fit the screens
3. If something in the design must change, comment in pull request #4 now. Later changes are possible, but each one needs a new migration

## Next tasks (Week 1, Oct 12 to 18)

| No. | Task | Owner | Depends on |
|---|---|---|---|
| 1 | Review pull requests #3, #4 and #5 | LMHP, SWYH, ANK | Nothing |
| 2 | Placeholder endpoints that return the contract's example JSON, so the app can connect early | HP | Nothing |
| 3 | Real sign up and login endpoints (Section 1), with password hashing | HP | Task 1 (#5 merged) |
| 4 | Design system and onboarding and dashboard screens, using the contract's examples as fake data | LMHP | Nothing |
| 5 | One complete sample unit in the contract format | ANK | Nothing |
| 6 | First proverb list (effort, consistency, never giving up, not wasting time) | ANK | Nothing |
| 7 | Compare LLMs, then agree with HP on the AI functions for More examples and Why? | SWYH | Nothing |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test template (ANK to confirm against the N1 format)
3. How last level and score change the daily pace (HP to propose)
4. Which LLM to use (SWYH to propose)
5. Daily limit for More examples, currently 50 (team to decide after testing)
6. Quiz question bank size, so retakes get a different mix (ANK, suggestion: 40 per quiz)
7. When content is corrected, should saved "Why?" explanations for that question be regenerated? (HP and SWYH, suggestion: yes)
8. If someone signs up with email, then later uses Google with the same email, join the accounts or refuse? (HP to propose. Joining only when Google says the email is verified)
