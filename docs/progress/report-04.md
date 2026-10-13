# Progress Report No. 04 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 13, 2026 (afternoon and evening, after Report No. 03) | 2026-10-13 | HP (Backend and Infrastructure) |

## Summary

All 37 endpoints from the API contract now exist as placeholders that return the contract's example JSON, so the app can connect to the real backend today.
HP reviewed the first pull requests from every teammate: LMHP's Expo setup and SWYH's LLM comparison are merged, and ANK's Unit 1 sample is waiting for its JSON version.
The app now has a name: **急合 (きゅうごう, Kyugo)**, meaning "fast pass".

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | Placeholder endpoints for all 37 contract endpoints, in 4 files matching the contract's 4 sections | In review (pull request #8) |
| 2 | Request shapes checked automatically: wrong fields or values are refused with 422 | In review (pull request #8) |
| 3 | Start quiz (#19) and start mock test (#23) never include correct answers | In review (pull request #8) |
| 4 | `/docs` page shows all endpoints in 4 groups, in contract order, each labeled with its contract number | In review (pull request #8) |
| 5 | Reviewed LMHP's Expo setup (#7): 4 fixes requested, all fixed, approved | Merged |
| 6 | Reviewed SWYH's LLM comparison (#9): follow-ups listed for SWYH | Merged |
| 7 | Reviewed ANK's Unit 1 sample (#11): approval held until the JSON version is added; AI prompt prepared to convert it | Open |
| 8 | Found that the Team Brief PDF is out of date (still says "N1 and N2") | Fix planned |

## Placeholder endpoints at a glance

| Section | File | Endpoints |
|---|---|---|
| 1. Onboarding | `backend/app/api/v1/onboarding.py` | #1 to #10 |
| 2. Dashboard, sessions and units | `backend/app/api/v1/dashboard.py` | #11 to #18 |
| 3. Quiz and mock test | `backend/app/api/v1/exams.py` | #19 to #26 |
| 4. AI and settings | `backend/app/api/v1/settings.py` | #27 to #37 |

What "placeholder" means:

- No database, no login check and no AI call yet. Each endpoint always returns the same example.
- When an endpoint gets its real logic, its address and answer shape stay the same, so the app does not need to change.
- Dangerous actions need a typed confirmation: `"DELETE"` to delete the account, `"RESET"` to reset progress.

How to try it: `docker compose up --build`, then open http://localhost:8000/docs.

Base URL for the app:

| Where the app runs | Base URL |
|---|---|
| Web browser or iOS simulator | `http://localhost:8000/api/v1` |
| Android emulator | `http://10.0.2.2:8000/api/v1` |
| Real phone | Not reachable yet. The backend only accepts connections from the same computer (a security setting). HP sets up a safe way when needed |

## Team highlights: the first day everyone's work landed

| Member | What they did | Status |
|---|---|---|
| LMHP | Set up the Expo app: TypeScript (strict), Expo Router for screens, folders for the API, fake data, theme and components. Wrote a project README and linked the team rules in `frontend/AGENTS.md` | Merged (#7) |
| SWYH | Compared a local model (qwen2.5:7b) and a cloud model (gemini-2.5-flash) on 5 N1 questions with the same prompt and our JSON shape. Gemini: natural Burmese, correct explanations, about 7 seconds. Local model: about 138 seconds and unusable Burmese. Kept a prompt log | Merged (#9) |
| ANK | Made a Unit 1 sample with Claude: 20 N1 words and 〜をものともせず, each with readings, Burmese meanings and 3 example sentences | Open (#11), JSON version next |

## Decisions made

| Area | Decision |
|---|---|
| App name | **急合 (きゅうごう, Kyugo)**, meaning "fast pass". In `app.json`: name "急合", slug and scheme "kyugo" |
| Learning content | Stored as JSON only, one file per unit: `data/units/s01_u01.json` to `data/units/s20_u10.json`. No PDFs for units |
| PDFs in the repo | Only for progress reports (they never change after writing). Living documents (brief, roles, contract, design) are Markdown only |
| Reviews | When possible, wait for both reviewers before merging. Changes to real backend code or security wait for HP |
| Future reports | One team report written by HP, with a short section per member that each person checks in the pull request |

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review and merge pull request #8 (placeholder endpoints) | LMHP, SWYH |
| 2 | Connect the app to the placeholder endpoints | LMHP |
| 3 | Update `app.json` to 急合 (kyugo), and remove unused template images | LMHP |
| 4 | Add Unit 1 as JSON to pull request #11, and remove the PDF | ANK |
| 5 | LLM follow-ups: move test files out of `backend/app/`, handle "Why?" when the answer was correct, test one newer Gemini model | SWYH |
| 6 | Remove the outdated Team Brief and Team Roles PDFs, and add the app name to `docs/project-brief.md` | HP |
| 7 | Real sign up and login endpoints (Section 1), with password hashing | HP |

## Open decisions

1. Pass prediction formula (HP and ANK to propose)
2. Exact question split in the mock test template (ANK to confirm against the N1 format)
3. How last level and score change the daily pace (HP to propose)
4. Which LLM to use: gemini-2.5-flash recommended by SWYH, final choice after testing one newer model
5. Daily limit for More examples, currently 50 (team to decide after testing)
6. Quiz question bank size, so retakes get a different mix (ANK, suggestion: 40 per quiz)
7. When content is corrected, should saved "Why?" explanations be regenerated? (HP and SWYH, suggestion: yes)
8. If someone signs up with email, then later uses Google with the same email, join the accounts or refuse? (HP to propose)
9. Add a Japanese definition field (`meaning_ja`) to the contract? (team, ANK's sample shows it is useful)
10. Environment setting names for the AI key: keep `LLM_API_KEY` and add `LLM_MODEL`? (HP and SWYH)
11. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
