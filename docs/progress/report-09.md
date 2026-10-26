# Progress Report No. 09 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 24 to Oct 25, 2026 | 2026-10-25 | HP (Backend and Infrastructure) |

## Summary

The backend is almost feature complete. The mock test is merged. More examples, forgot password, change password,
the daily study reminder and everything needed to put the backend online for free are built and in review.
The main target is now the **iOS app**, so Google login is moved to the public release.
Session 2 has 3 units. **The biggest blocker is still content: there are no quiz questions yet,
so every user stops after Unit 5 of Session 1.**

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | Mock test (contract #23 to #26): server clock, automatic submit at the end time, resume, retakes | Merged (#54) |
| 2 | Contract: which parts can be missing while content is still being added | Merged (#60) |
| 3 | Every content file is checked automatically on every pull request | Merged (#61) |
| 4 | Optional setting to test the app on a phone over home Wi-Fi | Merged (#67) |
| 5 | Change password (contract #34), contract v0.7 | In review (#57) |
| 6 | "More examples" (contract #27) with SWYH's AI function and a daily limit of 50 taps | In review (#65) |
| 7 | Forgot password with a 6-digit code by email (contract #5, #6) | In review (#66) |
| 8 | Library updates (FastAPI 0.162, SQLAlchemy 2.1.6) and httpx2 for tests | Approved (#70) |
| 9 | Ready for the online server: Render + Neon + UptimeRobot, all free, with a setup guide (`docs/deploy.md`) | Approved (#71) |
| 10 | Content loaders turn ～ into 〜 automatically | Approved (#72) |
| 11 | Quiz and mock test files share one set of question rules | In review (#73) |
| 12 | Daily study reminder as a push notification | In review (#74) |
| 13 | Loaded Session 2, Units 1 to 3 into the database (13 units in total) | Done |
| 14 | Reviewed team work: #58, #62, #63, #64, #68, #69 | Done |

Automated tests: 357 on main today, 449 when all open backend pull requests are merged.

## Security at a glance (new this time)

| Protection | What it stops |
|---|---|
| Forgot password gives the same answer for every email | Finding out who has an account |
| Reset code: 6 digits, 15 minutes, works once, only a keyed hash is stored, 5 wrong tries and it stops working | Guessing the code, or using a copy of the database to work it out |
| Limits on asking for codes (per email and per network) | Flooding someone's inbox |
| A new password signs out every device | A thief staying logged in |
| Per-network limits read only the address added by Render (`PROXY_HOPS`) | Getting extra tries with a fake address |
| "More examples": 50 taps per user per day, a failed AI call gives the tap back | Running up the AI bill |
| Push tokens are never written in full to the log. Each reminder is sent at most once a day | Leaking phone tokens, spamming users |
| Secrets only on Render's Environment page, a new `JWT_SECRET` for the server | Keys ending up in GitHub or chat |

## Team highlights

| Member | What they did | Status |
|---|---|---|
| LMHP | Connected log in, setup, plan, Home, units and saved words to the real backend (#58) | Merged |
| LMHP | Settings screens (#62). "Studied" marks for words and grammar (#68) | Merged |
| LMHP | Saved words as a folding notebook (#69). Asked to move the Expo 57 to 58 upgrade into its own pull request | Waiting |
| LMHP | Reviewed and approved #70, #71, #72 | Done |
| SWYH | `generate_examples()` for "More examples", with a furigana check (#63) | Merged |
| ANK | Session 2, Unit 3 (#64) | Merged |

## Content status

| Session 1 unit | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Status | Done | Done | Done | Done | Done | Done | Done | Done | Done | Done |

- Session 2: Units 1 to 3 done.
- 13 of 200 units (6.5%), 260 words.
- **No quiz questions yet.** Units 6 to 10 stay locked until Quiz 1 exists. A guide for drafting quiz questions with AI was shared with ANK. This is the most urgent content task.
- No mock test or proverb files yet. The formats and loaders are ready.

## Decisions made

| Area | Decision |
|---|---|
| Main target | The iOS app |
| Login | Email only for now. Google login waits for the public release, together with Sign in with Apple (the App Store requires it when Google login is offered) |
| Forgot password | A 6-digit code by email (Resend). Codes only go to the backend log (`EMAIL_MODE=log`) until we have our own email domain |
| Hosting | $0: Render (backend), Neon (database), UptimeRobot (keeps it awake) |
| "More examples" | 50 taps per user per day (team to adjust after testing) |
| Study reminder | Sent at the user's reminder time, up to 30 minutes late, never later. Not sent on a day the user already studied |
| Wave dash | The loaders fix ～ automatically, so content files don't break |
| Pass prediction (draft, ANK to confirm) | Latest 2 mock tests, first tries only. 70% Language Knowledge, 30% Reading. Listening is not part of the app |

## Action needed (everyone)

After pulling main, copy any new lines from `.env.example` into your own `.env`, then update your database:

```
docker compose run --rm --build backend alembic upgrade head
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
```

If tests stop with `Can't locate revision identified by ...`, your test database is ahead of your branch. Reset it (only the test database is deleted):

```
docker compose exec db dropdb -U jlpt jlpt_test
```

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review #57, #59, #65, #66, #73, #74 (SWYH: #65, ANK: #73 and the Burmese reminder text in #74) | Team |
| 2 | Merge #70, #71, #72, then put the backend online (`docs/deploy.md`) | HP |
| 3 | Quiz 1 and Quiz 2 questions for Session 1 (most urgent) | ANK, Deedeedar |
| 4 | Mock test for Session 1, following `docs/mock-test-format.md` | ANK, Deedeedar |
| 5 | Split the Expo upgrade out of #69. Then connect the quiz, "Why?", "More examples", mock test, forgot and change password, and ask for notification permission (#33) | LMHP |
| 6 | Pass prediction formula: ANK confirms the draft, then HP builds it | ANK, HP |

## Open decisions

1. Pass prediction formula (draft sent to ANK)
2. Reading questions in the mock test: 1 for the short passage, 3 for the medium, 4 for the long (ANK to confirm)
3. Proverb of the day notification: what time to send it
4. Our own email domain, so reset codes can really be emailed
5. Push notifications on real phones: Expo Go on Android doesn't support them, so a development build is needed (LMHP to check iOS)
6. Add a Japanese definition field (`meaning_ja`) to the contract? (team)
7. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
