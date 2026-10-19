# Progress Report No. 06 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 15 to Oct 17, 2026 | 2026-10-17 | HP (Backend and Infrastructure) |

## Summary

GitHub now runs our automated tests on every pull request, and a pull request can't be merged unless they pass.
Setup (onboarding) and the study plan are real. Rate limits and the study screens (session, unit, "Mark as done") are built and waiting for review.
The content team delivered 6 units of Session 1, and all 120 words load into the database.
LMHP renamed the app to 急合 (Kyugo), and SWYH finished the AI follow-ups.

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | GitHub automatic checks: the tests run on every pull request. Merging is blocked until they pass (ruleset) | Merged (#18) |
| 2 | Real setup and study plan (contract #9, #10), contract v0.4, 23 new tests | Merged (#21) |
| 3 | Progress Report 05 | Merged (#17) |
| 4 | Rate limits on log in and sign up, contract v0.5, 9 new tests | In review (#29) |
| 5 | Real session, unit and "Mark as done" (contract #13, #14, #15) with the unlock rules, 21 new tests | In review (#30) |
| 6 | Loaded Units 1 to 5 and 7 into the database and checked them: 120 words | Done |
| 7 | Reviewed 9 pull requests from the team (#19, #20, #22 to #28) | Done |

Automated tests: 52 on main today, 82 when #29 and #30 are merged.

## Security at a glance (new this time)

| Protection | What it stops |
|---|---|
| Tests must pass before merging | Broken login or security code reaching main by accident |
| 5 wrong passwords per email in 15 minutes, 30 log in tries per network in 5 minutes | Password guessing |
| 20 sign ups per network per hour | Bots creating fake accounts |
| Unknown emails are limited the same way | Finding out who has an account |
| Unlock rules checked on the server | Opening locked units, quizzes or sessions by calling the API directly |
| Strict input checks (scores, dates, ids) | Crashes and odd data from bad or hostile requests |

## Team highlights

| Member | What they did | Status |
|---|---|---|
| LMHP | Set the app name to 急合, slug and scheme `kyugo` (#19). Removed 14 unused template images and fixed the README (#28), on a fresh branch | Merged |
| SWYH | Moved the AI test scripts out of the app to `backend/scripts/ai_eval/`. Prompt v3 handles "the user answered correctly" (returns `null`), proven by a new test question. Added automatic retry when Gemini is busy (#26) | Merged |
| ANK | Units 1, 3, 4 and 5 of Session 1 as JSON (#20, #23, #24, #25). All readings correct, checked with the loader | Merged |
| Deedeedar (new) | Units 2 and 7 of Session 1 (#22, #27). Fixed the 恵み meaning after review | Merged |

## Content status

| Session 1 unit | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Status | Done | Done | Done | Done | Done | To do | Done | To do | To do | To do |

- 6 of 200 units (3%). Grammar so far: 〜をものともせず, 〜ならでは, 〜を皮切りに, 〜をよそに, 〜にかたくない, 〜ずにはおかない
- No quiz questions yet. Until Quiz 1 exists, units 6 to 10 stay locked for everyone (the rule working correctly)

## Decisions made

| Area | Decision |
|---|---|
| Merging | Tests must pass (green check) before any pull request can be merged |
| Setup answers | A score is needed for N1 and N2. "Today" means Japan time (contract v0.4) |
| Rate limits | Values above, written into contract v0.5. The app shows a Burmese "please wait" message on 429 |
| Content style | Verbs in dictionary form (促す, not 促). Wave dash 〜 (U+301C) only, never ～. Words found on both N1 and N2 lists are fine |
| AI key names | `LLM_API_KEY` and `LLM_MODEL` everywhere (was open decision #9) |
| Branches | Every new task starts on a new branch from main. Don't reuse merged branches |

## Action needed (everyone)

Load the latest units into your own database after pulling main:

```
docker compose run --rm --build backend alembic upgrade head
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
```

Content team: run the same command with `--check` before opening a pull request.

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review #29 (rate limits) and #30 (session and unit screens) | LMHP, SWYH |
| 2 | Units 6, 8, 9 and 10 of Session 1. Decide who does Unit 6 | ANK, Deedeedar |
| 3 | Quiz question format (JSON) and a quiz loader | HP |
| 4 | Quiz 1 questions for Session 1 (units 1 to 5), in that format | ANK, Deedeedar |
| 5 | Quiz endpoints (#19 to #22) | HP |
| 6 | Connect the app to the real backend: log in, setup, plan, session and unit screens | LMHP |
| 7 | Real AI functions for "More examples" and "Why?", using `LLM_API_KEY` and `LLM_MODEL`. Test one newer Gemini model | SWYH |
| 8 | Dashboard, proverb of the day and saved words (#11, #12, #16 to #18) | HP |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test template (ANK to confirm against the N1 format)
3. Which LLM to use: gemini-2.5-flash for now, final choice after testing one newer model (SWYH)
4. Daily limit for More examples, currently 50 (team to decide after testing)
5. Quiz question bank size, so retakes get a different mix (ANK, suggestion: 40 per quiz)
6. When content is corrected, should saved "Why?" explanations be regenerated? (HP and SWYH, suggestion: yes)
7. If someone signs up with email, then later uses Google with the same email, join the accounts or refuse? (HP to propose)
8. Add a Japanese definition field (`meaning_ja`) to the contract? (team)
9. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
