# Progress Report No. 05 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 13 (night) to Oct 14, 2026 | 2026-10-14 | HP (Backend and Infrastructure) |

## Summary

Real sign up and login are built, with strong security and 21 automated tests that attack them on purpose.
The content loader and the study plan math are ready and waiting for review.
The official exam date list was removed: users now pick any future date.
A new member joined to help ANK with content.

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | Removed the official exam date list: contract v0.2, database design v0.2 (26 tables), migration, placeholder removed | Merged (#13) |
| 2 | Placeholder endpoints (now 36) | Merged (#8) |
| 3 | Progress Report 04 | Merged (#12) |
| 4 | Real sign up, log in, refresh, log out and "who am I" (contract #1, #2, #3, #7, #35) | In review (#14) |
| 5 | Every error now uses the contract format; crashes never show internal details | In review (#14) |
| 6 | Automated tests: 21 tests on a separate test database, run with one command | In review (#14) |
| 7 | Content loader: checks unit JSON files and loads them into the database | In review (#15) |
| 8 | Study plan math, 8 tests, and contract v0.3 (open question #3 decided) | In review (#16) |
| 9 | Closed ANK's PDF pull request (#11); Unit 1 is being redone as JSON | Done |

## Login security at a glance

| Protection | What it stops |
|---|---|
| Passwords stored only as Argon2 hashes | A stolen database can't reveal passwords |
| Access token (15 minutes), signed with a secret key | Fake or edited logins |
| Refresh token (30 days), works only once, stored only as a hash | Stolen tokens: reusing an old one signs out every session of that user |
| Same answer and similar time for "wrong password" and "unknown email" | Finding out who has an account |
| Input checks and SQLAlchemy parameters | SQL injection and oversized input |
| Contract-format errors, generic 500 | Leaking internal details |

All of these are checked by the automated tests.

## Content loader at a glance

- Checks every unit file before saving: 20 words, readings only on kanji (hiragana), Burmese where required, no unknown fields, file name matches the unit
- If any file has a problem, nothing is saved and the exact problem is printed
- Safe to run again: each unit has its own place, and words keep their ids, so saved words never break
- Content team check (changes nothing): `docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units --check /data/units`

## Study plan rule (contract v0.3)

Units left ÷ study days, rounded up, between 1 and 20 per day. The last days before the exam stay free for review and mock tests: 7 days if the user already took N1, 14 days otherwise. No exam date: 3 per day.

Example, exam on Dec 6: N1 → 5 per day, done by Nov 22. N2 or not taken → 6 per day, done by Nov 16.

## Team update

- A new member joined and helps ANK with content. First task: Unit 1 as JSON, from ANK's PDF sample
- LMHP's Expo setup (#7) and SWYH's LLM comparison (#9) were merged on Oct 13

## Decisions made

| Area | Decision |
|---|---|
| Exam date | No official list. The user picks any future date, or "not decided yet", and can change it in Settings (#29). Reason: the list needed manual updates every year, and some cities outside Japan hold only one test a year |
| Study plan | Rule above, written into contract v0.3 |
| Database | HP keeps handling the database |
| Unit 1 | Redone as JSON by the new member; the PDF does not go into the repo |

## Action needed after #14 is merged (everyone)

Login needs a secret key in your own `.env`. Run this once in the repo folder:

```
echo "JWT_SECRET=$(python3 -c 'import secrets; print(secrets.token_urlsafe(48))')" >> .env
```

Then restart with `docker compose up --build -d`. Never share or commit this value.

Run the tests with: `docker compose --profile test run --rm --build tests`

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review #14 (login and tests). It blocks most backend work | LMHP, SWYH |
| 2 | Review #15 (content loader) and #16 (study plan) | Team |
| 3 | GitHub automatic checks: run the tests on every pull request | HP |
| 4 | Real `/onboarding` and `/plan`, using the study plan math | HP |
| 5 | Rate limiting on login and sign up | HP |
| 6 | Update `app.json` to 急合 (kyugo), and connect the app to the backend | LMHP |
| 7 | Unit 1 as JSON (pull request), reviewed by ANK | New member, ANK |
| 8 | LLM follow-ups from #9 | SWYH |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test template (ANK to confirm against the N1 format)
3. Which LLM to use: gemini-2.5-flash recommended, final choice after testing one newer model (SWYH)
4. Daily limit for More examples, currently 50 (team to decide after testing)
5. Quiz question bank size, so retakes get a different mix (ANK, suggestion: 40 per quiz)
6. When content is corrected, should saved "Why?" explanations be regenerated? (HP and SWYH, suggestion: yes)
7. If someone signs up with email, then later uses Google with the same email, join the accounts or refuse? (HP to propose)
8. Add a Japanese definition field (`meaning_ja`) to the contract? (team)
9. Environment setting names for the AI key: keep `LLM_API_KEY` and add `LLM_MODEL`? (HP and SWYH)
10. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
