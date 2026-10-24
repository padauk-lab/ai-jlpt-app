# Progress Report No. 07 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 18 to Oct 19, 2026 | 2026-10-19 | HP (Backend and Infrastructure) |

## Summary

The quiz is almost complete. The quiz question format and loader are merged, and the quiz endpoints (start, answer, finish, review) are built and in review.
The Settings screen, proverb of the day, rate limits and the session and unit screens are now real on main.
Saved words is built and in review. The mock test format and loader are merged, and GitHub now checks unit files on every pull request.
SWYH merged the first real AI function (the "Why?" button) and chose gemini-3.8-flash. LMHP merged the design system and the login screen.
Session 1 now has 7 units (140 words).

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | Rate limits on log in and sign up (contract v0.5) | Merged (#29) |
| 2 | Real session, unit and "Mark as done" (contract #13 to #15) with the unlock rules | Merged (#30) |
| 3 | Progress Report 06 | Merged (#31) |
| 4 | Quiz question format, quiz loader and content guide (`docs/content-format.md`) | Merged (#33) |
| 5 | Real Settings endpoints (contract #29 to #33, #36, #37): profile, notifications, devices, delete account, start over | Merged (#34) |
| 6 | Proverb of the day: format guide, loader and endpoint (contract #12) | Merged (#36) |
| 7 | GitHub now checks every unit file automatically on each pull request | Merged (#37) |
| 8 | Mock test format guide and loader (`docs/mock-test-format.md`) | Merged (#38) |
| 9 | Saved words (contract #16 to #18): list with search, save, remove. 27 new tests | In review |
| 10 | Quiz endpoints (contract #19 to #22): start, answer, finish, review. 20 new tests | In review |
| 11 | Reviewed team work: #35, #39, #41, #42 and issue #44 | Done |

Automated tests: 204 on main today, 251 when saved words and the quiz endpoints are merged.

## Security at a glance (new this time)

| Protection | What it stops |
|---|---|
| Correct answers are never sent before the user answers | Cheating by reading the answer from the app's network traffic |
| One answer per question, checked on the server and in the database | Answering again after seeing the result |
| A quiz attempt can only be read by its owner (403 otherwise) | Seeing other users' answers and scores |
| Words in a locked unit can't be saved (403) | Reading locked content through saved words |
| Delete account needs the password and typing "DELETE" | Deleting an account by accident or from a stolen phone |
| At most 10 devices per user | Filling the database with fake devices |
| AI answers are checked in code before users see them | Broken or wrong-format AI output reaching users |

## Team highlights

| Member | What they did | Status |
|---|---|---|
| LMHP | Design system, logo component and font loading. Login screen UI with a `RubyText` component for furigana (#35) | Merged |
| SWYH | Compared gemini-3.8-flash with gemini-2.5-flash and switched to `LLM_API_KEY`. Built `explain_answer()` for the "Why?" button, with output checks and tests (#42). Opened a plan for "More examples" (issue #44) | Merged |
| Deedeedar | Unit 8 of Session 1 (#41) | Merged |

## Content status

| Session 1 unit | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| Status | Done | Done | Done | Done | Done | To do | Done | Done | To do | To do |

- 7 of 200 units (3.5%), 140 words. New grammar: 〜ともなると
- No quiz questions yet. Until Quiz 1 exists, units 6 to 10 stay locked for everyone (the rule working correctly)
- No proverbs or mock test files yet. The formats and loaders are ready

## Decisions made

| Area | Decision |
|---|---|
| AI model | gemini-3.8-flash, with gemini-2.5-flash as the fallback (was open decision 3) |
| Quiz bank | 20 to 100 questions per quiz. Each attempt picks a random 20, so retakes get a different mix (was open decision 5) |
| Quiz units | Quiz 1 only covers units 1 to 5, Quiz 2 only units 6 to 10. The loader refuses anything else |
| Corrected content | When a question changes, its saved "Why?" answers are deleted and made again (was open decision 6) |
| Quiz review | Correct answers are shown only after finishing. Retakes are allowed and the best score counts |
| Unit files | Keep the flat `data/units/sNN_uMM.json` names (no session folders) |

## Action needed (everyone)

Update your own database after pulling main:

```
docker compose run --rm --build backend alembic upgrade head
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
```

Content team: GitHub now checks unit files for you on every pull request. A red X means a file has a problem; open the check to see which one.

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review the saved words and quiz endpoints pull requests | LMHP, SWYH |
| 2 | Units 6, 9 and 10 of Session 1. Decide who does Unit 6 | ANK, Deedeedar |
| 3 | Quiz 1 questions for Session 1 (units 1 to 5), following `docs/content-format.md` | ANK, Deedeedar |
| 4 | "Why?" endpoint (#28), using `explain_answer()`, saved answers and a shorter wait | HP |
| 5 | `generate_examples()` for "More examples" (issue #44) | SWYH |
| 6 | "More examples" endpoint (#27) with the daily limit, after task 5 | HP |
| 7 | Mock test endpoints (#23 to #26): server timer, auto submit, resume | HP |
| 8 | Connect the app to the real backend: log in, setup, plan, session and unit screens | LMHP |
| 9 | Dashboard (#11) and change password (#34) | HP |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test (the format allows 45 questions plus 3 reading passages; ANK to confirm against the N1 format)
3. Daily limit for "More examples", currently 50 (team to decide after testing)
4. Furigana in "More examples": written by the AI or added by a code tool (SWYH, after testing)
5. If someone signs up with email, then later uses Google with the same email, join the accounts or refuse? (HP to propose)
6. Add a Japanese definition field (`meaning_ja`) to the contract? (team)
7. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
