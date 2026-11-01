# Progress Report No. 10 (HP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 26 to Oct 30, 2026 | 2026-10-30 | HP (Backend and Infrastructure) |

## Summary

**The app runs on a real iPhone, with a real online server.** The backend is online for $0 (Render + Neon + UptimeRobot), and the whole team can use it from any network.
The app now has **10 sessions** (100 units, 2,000 core N1 words). Sessions 1 to 3 are complete (600 words), and Session 1 has both quizzes.
The pass prediction and the AI study tip are built. A security test on the online server found a real weakness, and it is fixed.
**The biggest blocker now: the Session 1 mock test.** Without it, nobody can open Session 2.

## Completed by HP

| No. | Task | Status |
|---|---|---|
| 1 | Change password (#57), "More examples" with a daily limit (#65), forgot password with a 6-digit code (#66) | Merged |
| 2 | Library updates (#70), wave dash fix (#72), shared question rules (#73) | Merged |
| 3 | Daily study reminder as a push notification (#74) | Merged |
| 4 | 10 sessions instead of 20 (#76) | Merged |
| 5 | Backend online: Render (server), Neon (database), UptimeRobot (keeps it awake), all free (#71, #80) | Live |
| 6 | Security fix: the login limit now sees each user's real address behind Cloudflare (#79) | Merged and tested online |
| 7 | Pass prediction from mock tests, contract v0.8 (#95) | Merged |
| 8 | AI study tip connected to the study plan (#97) | In review |
| 9 | Loaded 30 units and the Session 1 quizzes into the online database | Done |
| 10 | Gemini key on the server (only on Render, never in code), web testing allowed (CORS) | Done |
| 11 | Expo organization `padauk-lab`, so the app belongs to the team, not one person | Done |
| 12 | Reviewed team work: #69, #78, #81 to #94, #96 | Done |

Automated tests: 513 on main today, 525 when #97 is merged.

## Security at a glance (new this time)

| Protection | What it stops |
|---|---|
| The login limit reads the address Cloudflare writes itself (`cf-connecting-ip`), which nobody can fake. Tested online: 31 tries with fake addresses end with 429 | Guessing passwords on many accounts by faking addresses |
| Secrets only on Render's Environment page (encrypted). A separate Gemini key just for the server | Keys in GitHub, chat or the app |
| The AI key is never in the app: the app asks our server, the server asks Gemini | Anyone reading the key out of the app |
| Web access only from the team's own computers (`CORS_ORIGINS`) | Other websites using our server |
| The pass prediction and the study tip are calculated on the server | Faking a better result in the app |

## Team highlights

| Member | What they did | Status |
|---|---|---|
| LMHP | Saved words notebook (#69), Expo SDK 58 (#78), ox cart loading screen (#83) | Merged |
| LMHP | Quiz and "Why?" connected to the real backend (#94) | Merged |
| SWYH | `plan_tip()`, the AI study tip, with checks that the tip is Burmese and has no numbers (#96) | Merged |
| ANK | Session 1 Quiz 1 and Quiz 2, 80 questions (#82). Agreed the pass prediction formula | Merged |
| Deedeedar | Session 2 Units 4 to 10 (#81), Session 3 Units 1 to 10 (#84 to #93) | Merged |

## Content status

| Session | 1 | 2 | 3 | 4 to 10 |
|---|---|---|---|---|
| Units | 10 of 10 | 10 of 10 | 10 of 10 | Not yet |
| Quizzes | Done | Not yet | Not yet | Not yet |
| Mock test | **Missing** | Not yet | Not yet | Not yet |

- 30 of 100 units (30%), 600 words, 30 grammar patterns. No repeated words or grammar.
- **The Session 1 mock test is the most urgent task.** Every user stops at the end of Session 1 without it.
- No proverb files yet. The format and loader are ready.

## Decisions made

| Area | Decision |
|---|---|
| App size | 10 sessions, 100 units, 2,000 core N1 words for learners who already have N2 |
| Hosting | $0: Render, Neon, UptimeRobot. The free server is kept awake |
| Expo | Stay on SDK 58 (don't go back). The app belongs to the Expo organization `padauk-lab` |
| Pass prediction | Latest 2 mock tests, first tries only, newer one 60%. Score = 70% language knowledge + 30% reading. 60% = 50 chance, 2.5 per point, between 5 and 95. A section under 32% caps it at 15, with a warning. No listening |
| Mock test reading | 1, 3 and 4 questions (short, medium, long) |
| Study tip | Written after the plan is saved, wait at most about 8 seconds, never with numbers |
| Email check at sign-up | Not now. Add email verification before the public release |

## Action needed (everyone)

After pulling main:

```
cd frontend && npm install
docker compose run --rm --build backend alembic upgrade head
```

To test against the online server, in `frontend/.env.local`:

```
EXPO_PUBLIC_API_URL=https://kyugo-api.onrender.com/api/v1
```

Then start Expo with the cache cleared (`npx expo start -c`) and **sign up a new account**: the online database is separate from your laptop.

## Next tasks

| No. | Task | Owner |
|---|---|---|
| 1 | **Session 1 mock test** (`docs/mock-test-format.md`, reading 1, 3 and 4) | ANK, Deedeedar |
| 2 | Quiz 1 and Quiz 2 for Sessions 2 and 3 | ANK, Deedeedar |
| 3 | Connect the mock test, "More examples", forgot and change password. Show the pass prediction warning and the no-listening note | LMHP |
| 4 | A 15-second time limit on app requests, so a bad connection shows a message instead of spinning | LMHP |
| 5 | Ask for notification permission and register the phone (#33) | LMHP |
| 6 | Review and merge #97, Report 11 | HP |

## Open decisions

1. Proverb of the day notification: what time to send it
2. Our own email domain, so reset codes really reach inboxes (needed before the public release)
3. When to get the Apple Developer membership ($99 a year, needed to publish)
4. Shuffle the answer choices in quizzes (later, small)
5. Add a Japanese definition field (`meaning_ja`) to the contract? (team)
6. Keep `frontend/.claude/settings.json` (an AI tool setting) in the repo? (team)
