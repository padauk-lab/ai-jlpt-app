# Progress Report No. 11 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 31 to Nov 6, 2026 | 2026-11-06 | HP (Backend and Infrastructure) |

## Summary

**All 2,000 words are written, and Sessions 1 to 3 can be studied from start to finish.** Deedeedar finished every unit for Sessions 5 to 10, and the whole word list has no repeats.
The Session 1 to 3 quizzes and mock tests are in the online database, so a user can now go from Session 1 all the way to the Session 3 mock test. Session 4's quizzes and mock test are in review.
LMHP's review found two real problems (a mock question that copied a quiz, and an AI crash on the server). Both are fixed.
**The next big step: quizzes and mock tests for Sessions 5 to 10, and the mock test screen in the app.**

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | AI study tip on the study plan (#97), LMHP's review comment fixed | Merged |
| 2 | Backend cleanup: the database allows only sessions 1 to 10, /health listed once in the API docs (#111) | Merged |
| 3 | Session 1 mock test (#112). Fixed 4 questions that repeated quiz sentences (found by LMHP) | Merged |
| 4 | Session 2 quizzes and mock test (#113), Session 3 quizzes and mock test (#114) | Merged |
| 5 | Session 4 quizzes and mock test (#118) | In review |
| 6 | AI fix: a missing AI setting now answers 503 "try again later" instead of crashing with 500 (#119, found by LMHP) | In review |
| 7 | Checked all 60 unit pull requests from Deedeedar (#120 to #179): file names, numbers, readings, examples, no repeats | Done |
| 8 | Merged 58 units, loaded 98 units, 6 quizzes and 3 mock tests into the online database | Done |
| 9 | Handoff file for AI assistants saved in the project, so a lost chat costs nothing | Done |

Automated tests: 528 on main today, 530 when #119 is merged.

## How the quizzes and mock tests are made

| Item | Rule |
|---|---|
| Quiz | 40 questions per quiz, 8 per unit: 2 kanji reading, 2 context, 1 paraphrase, 1 usage, 1 grammar form, 1 sentence order. A test picks 20 at random |
| Mock test | 45 language knowledge questions in the official N1 split (kanji 6, context 7, paraphrase 6, usage 6, grammar form 15, sentence order 5), plus readings with 1, 3 and 4 questions |
| No repeats | Mock test words never appear in that session's quizzes. Each grammar pattern appears twice. Mock sentences are compared with quiz sentences |
| Fair answers | Answers spread evenly over a to d. Patterns with the same meaning (が早いか, なり, や否や) are never wrong options for each other |
| Checks | The content checker (`check_all`), a test load, and a review sheet with the answers marked for HP (N1) |

## Content checks on Sessions 5 to 10 (new this time)

| Check | Result |
|---|---|
| 60 units, each title, file name and inside numbers match | All 60 correct |
| 20 words in every unit, no word or grammar pattern used twice in the whole app | 2,000 different words, 100 different patterns |
| Every word reading compared with a Japanese dictionary (MeCab with UniDic) | 27 differences, all 27 times the file was right |
| Each example sentence uses its own word | 2 problems: #142 (揚げる, example uses 揚がる) and #150 (連なる, example uses 連ねる) |

## Team highlights

| Member | What they did | Status |
|---|---|---|
| Deedeedar | Session 4 units (#102 to #110), Sessions 5 to 10, 60 units (#120 to #179). **All 2,000 words are done** | Merged (2 waiting for a small fix) |
| LMHP | Saved words as Burmese flash cards (#99), plan loading screen at least 3.5 seconds (#100) | Merged |
| LMHP | "More examples" on word and grammar cards (#115), hide Google login and the forgot-password link for now (#116), his first report (#117) | Merged |
| LMHP | Reviewed #97 and #111 to #114, and found the copied mock question and the AI crash | Done |

## Content status

| Session | 1 to 3 | 4 | 5 to 10 |
|---|---|---|---|
| Units | 30 of 30 | 10 of 10 | 58 of 60 (S7 U3 and S8 U1 waiting for a fix) |
| Quizzes | Done, online | In review (#118) | Not yet |
| Mock test | Done, online | In review (#118) | Not yet |

- 98 of 100 units are in the online database.
- A user can study from Session 1 to the Session 3 mock test today.
- No proverb files yet. The format and loader are ready.

## Lessons learned

| What happened | What we do now |
|---|---|
| Loading all units at once dropped the Neon connection twice (`SSL error: unexpected eof`). Nothing broke, because the loader saves all or nothing | Load one session at a time. Later: make the loader send fewer database requests |
| A mock test question copied a quiz sentence word for word | Compare mock sentences with quiz sentences, not only the words |
| An approval stayed valid after new code was pushed | Turn on "Dismiss stale pull request approvals when new commits are pushed" in the `protect-main` rules |
| 87 old branches made GitHub hard to read | Deleted the merged ones. Turn on "Automatically delete head branches" |

## Decisions made

| Area | Decision |
|---|---|
| Release | Team only for now, on Expo Go, $0. No App Store or TestFlight yet |
| Content making | HP makes the quizzes and mock tests with an AI assistant and reviews them as the N1 holder |
| Big reviews | `gh pr review --approve` in a loop, after the checks above |
| AI on the server | A missing AI setting means "AI off" (503), never a crash |

## Action needed

**HP:** add `LLM_MODEL` and `LLM_API_KEY` on Render (Environment page). Without them, every AI button answers "try again later".

**Everyone**, after pulling main (#111 added a database migration, so your local database needs it):

```
docker compose run --rm --build backend alembic upgrade head
```

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | Review #118 (Session 4) and #119 (AI fix) | SWYH, LMHP |
| 2 | Fix example 3 in #142 and #150 | Deedeedar |
| 3 | Quizzes and mock tests for Sessions 5 to 10 | HP (with ANK checking) |
| 4 | Mock test screen (#23 to #26), then forgot and change password screens | LMHP |
| 5 | Harder wrong options for the "usage" questions (LMHP: too easy for N1) | HP, ANK |
| 6 | Load units in fewer requests, Report 12 | HP |

## Open decisions

1. Proverb of the day notification: what time to send it
2. Our own email domain, so reset codes really reach inboxes (before the public release)
3. When to get the Apple Developer membership (about ¥12,800 a year, needed for TestFlight or the App Store)
4. Who writes the proverb file
