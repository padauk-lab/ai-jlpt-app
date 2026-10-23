# Progress Report No. 08 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 20 to Oct 23, 2026 | 2026-10-23 | HP (Backend and Infrastructure) |

## Summary

Session 1 is complete: 10 units, 200 words and 10 grammar patterns, all in the database. Session 2 has started (2 units).
The backend now has the real dashboard, the "Why?" button with the AI, saved words, the quiz, and a strict CORS setting for the web app.
The mock test and change password are built and in review. LMHP connected the app to the real backend (in review).
The biggest blocker now is content: there are no quiz questions yet, so every user stops after Unit 5 of Session 1.

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | Saved words (contract #16 to #18): list with search, save, remove | Merged (#43) |
| 2 | Quiz endpoints (contract #19 to #22): start, answer, finish, review | Merged (#45) |
| 3 | CORS: a strict list of web pages allowed to call the API, with fixes from the ANK team's review | Merged (#49) |
| 4 | Real dashboard (contract #11) for the Home map, contract v0.6 | Merged (#52) |
| 5 | "Why?" button (contract #28) with the AI: saved answers, at most about 45 seconds of waiting | Merged (#53) |
| 6 | Mock test (contract #23 to #26): server clock, automatic submit, resume, retakes | In review (#54) |
| 7 | Change password (contract #34), contract v0.7 | In review (#57) |
| 8 | Loaded all 10 units of Session 1 into the database and checked them | Done |
| 9 | Reviewed team work: #46 to #48, #50, #51, #55, #56, #58 | Done |

Automated tests: 299 on main today, 336 when #54 and #57 are merged.

## Security at a glance (new this time)

| Protection | What it stops |
|---|---|
| CORS allow list from `.env`: no "*", https only for real websites | Other websites using a logged-in browser to call our API |
| "Why?" only works after the user has seen the answer | Using the AI to get answers before answering |
| One AI answer per question and choice, saved and shared | Paying for the same AI answer again and again |
| The mock test clock is the server's. Late answers are refused | Cheating by changing the phone's clock |
| Change password needs the old one and shares the login guess limit | Guessing the password through Settings |
| Change password signs out every device | A thief who knew the old password staying logged in |
| Login tokens in the phone's secure storage, never in plain storage (also asked for web) | Other apps or scripts reading the user's login |

## Team highlights

| Member | What they did | Status |
|---|---|---|
| LMHP | Home map, unit flip cards, grammar, quiz, setup and plan screens (#47). Quiz result and review screens, iPhone text fix (#48) | Merged |
| LMHP | Connected log in, setup, plan, Home, units and saved words to the real backend (#58). Two small fixes asked (tokens on web, logout on server errors) | In review |
| ANK | Session 2, Units 1 and 2 (#55, #56). Unit 2 is a strong law and courts theme. Careful review of the CORS pull request found 3 real issues | Merged |
| Deedeedar | Session 1, Units 6, 9 and 10 (#46, #50, #51). This completed Session 1 | Merged |
| SWYH | Working on `generate_examples()` for "More examples" (issue #44) | In progress |

## Content status

| Session 1 unit | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Status | Done | Done | Done | Done | Done | Done | Done | Done | Done | Done |

- Session 2: Units 1 and 2 done.
- 12 of 200 units (6%), 240 words. New grammar: 〜をおいて, 〜を禁じ得ない, 〜ならいざ知らず, 〜をもって, 〜に至っては
- **No quiz questions yet.** Units 6 to 10 stay locked until Quiz 1 exists, so every user stops after Unit 5. This is the most urgent content task.
- No mock test or proverb files yet. The formats and loaders are ready.

## Decisions made

| Area | Decision |
|---|---|
| Web app access | Only the addresses in `CORS_ORIGINS` (in `.env`) may call the API from a browser |
| Dashboard | Sessions not loaded yet are shown locked, with `id: null` (contract v0.6) |
| "Why?" | Answers are saved and shared by everyone. Skipped questions in a finished quiz also work |
| AI waiting time | At most about 45 seconds, then "try again later" (503) |
| Mock test | Submitted automatically at the end time. Only the first attempt in a round counts for the prediction. `pass_prediction` stays empty until the formula is decided |
| Change password | Every device is signed out, and this phone gets a fresh login (contract v0.7) |
| Login on web | Tokens kept in memory only, never in `localStorage` |

## Action needed (everyone)

Add these two lines to your own `.env` (not only `.env.example`):

```
CORS_ORIGINS=http://localhost:8081
LLM_MODEL=gemini-3.8-flash
```

Then update your database after pulling main:

```
docker compose run --rm --build backend alembic upgrade head
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
```

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review the mock test (#54) and change password (#57) pull requests | LMHP, SWYH |
| 2 | Quiz 1 and Quiz 2 questions for Session 1, following `docs/content-format.md` (most urgent) | ANK, Deedeedar |
| 3 | Mock test for Session 1, following `docs/mock-test-format.md` | ANK, Deedeedar |
| 4 | Two fixes in #58, then connect the quiz, "Why?", mock test and change password | LMHP |
| 5 | `generate_examples()` for "More examples" (issue #44) | SWYH |
| 6 | "More examples" endpoint (#27) with the daily limit, after task 5 | HP |
| 7 | Safe setup for testing the app on a real phone | HP |
| 8 | Pass prediction formula | HP, ANK |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test (the format allows 45 questions plus 3 reading passages; ANK to confirm against the N1 format)
3. Daily limit for "More examples", currently 50 (team to decide after testing)
4. Furigana in "More examples": written by the AI or added by a code tool (SWYH, after testing)
5. If someone signs up with email, then later uses Google with the same email, join the accounts or refuse? (HP to propose)
6. Add a Japanese definition field (`meaning_ja`) to the contract? (team)
7. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
