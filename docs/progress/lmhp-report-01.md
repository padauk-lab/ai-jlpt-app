# Progress Report No. 01 (LMHP)

| Period | Date | Prepared by |
|---|---|---|
| Oct 13 to Nov 5, 2026 | 2026-11-05 | LMHP (Frontend and Design) |

## Summary

**Every main screen of the app is built, and most of them talk to the real backend.** A user can sign up, finish setup, see the study plan, follow the Home map, study units with flip cards, take quizzes with "Why?", save words as flash cards, and change settings, all against the online server.
The app runs on Expo SDK 58 and works on a real iPhone.
**The biggest screen still missing: the mock test** (#23 to #26). The backend is ready, and the Session 1 to 3 mock tests are in review (#112 to #114), so the screen is my next large task.

## Completed by LMHP

| No. | Task | PR | Status |
|---|---|---|---|
| 1 | Expo project in `frontend/`, app name and scheme, README | #7, #19, #28 | Merged |
| 2 | Login and sign-up screen, `RubyText` component for furigana | #35 | Merged |
| 3 | Home study map: Bagan background, torii gates for tests, bottom tabs | #47 | Merged |
| 4 | Unit flip cards, grammar card, quiz, setup and study plan screens | #47 | Merged |
| 5 | Fix Burmese serif text being cut off on iPhone | #48 | Merged |
| 6 | Connect login, setup, plan, Home, units and saved words to the real backend. Home works when a session has no mock test or quizzes yet (`id: null`, contract v0.6) | #58 | Merged |
| 7 | Settings: profile, study setup, notifications, username, reset progress, delete account | #62 | Merged |
| 8 | Unit: "studied" marks, Mark as done only when everything is studied, go to the next item | #68 | Merged |
| 9 | Saved words notebook, connected to bookmarks (#16 to #18) | #69 | Merged |
| 10 | Expo SDK 57 → 58 (React Native 0.88), as its own PR with `~` versions | #78 | Merged |
| 11 | Generating plan: ox cart traveling to the 合格 gate | #83 | Merged |
| 12 | Quiz and "Why?" connected to the real backend (#19 to #22, #28) | #94 | Merged |
| 13 | Saved words as traditional Burmese flash cards, with explanations and More examples (#27, including the 429 daily limit) | #99 | Merged |
| 14 | Generating plan screen shows for at least 3.5 seconds | #100 | Merged |
| 15 | "More examples" on unit word and grammar cards (#27), sharing one `useMoreExamples` hook with Saved words | #115 | In review |
| 16 | Hide the Google login button and the "forgot password" link with switches (App Store rule 4.8) | #116 | In review |

## Reviews

| PR | Note |
|---|---|
| #18, #20, #52, #54, #57, #60, #67, #70, #71, #72, #80 | Reviewed, checked against the contract and ran the tests |
| #97 | Found a bug: if the plan changes twice quickly while the AI is slow, the new plan gets no tip for an hour. Reproduced it with a test; HP fixed it in the same PR, and I checked the fix (13 of 13 tip tests, 526 in total) |
| #111 | Tested the new migration (sessions 1 to 10) up, down and up again on PostgreSQL; `alembic check` shows no differences |
| #112 to #114 | Checked all quizzes and mock tests with `check_all` and loaded them into a test database. Found that Session 1 mock #35 repeats Quiz 2 #39, and that the wrong options in the usage questions are too easy for N1 |

## Screen status

| Screen | Built | Real backend |
|---|---|---|
| Login and sign-up | Yes | Yes. Google button and forgot link hidden in review (#116) |
| First-time setup, Generating plan, Study plan | Yes | Yes (AI tip box shows when `ai_tip_my` is not null) |
| Home map and header | Yes | Yes |
| Unit (words and grammar) | Yes | Yes. "More examples" in review (#115) |
| Quiz, quiz review, "Why?" | Yes | Yes |
| Saved words (flash cards) | Yes | Yes, including "More examples" |
| Settings (all groups) | Yes | Yes |
| Mock test and result | **No** | Backend ready (#54) |
| Change password | **No** | Backend ready (#57) |
| Forgot password | **No** | Backend ready (#66) |

## Next tasks (LMHP)

| No. | Task | Priority |
|---|---|---|
| 1 | **Mock test screens** (#23 to #26): countdown from `server_time` and `ends_at`, restore `saved_answers`, `attempt_finished` opens the result, `submitted_by: "timeout"` message. Content for Sessions 1 to 3 is in review (#112 to #114) | High |
| 2 | `client.ts`: refresh the token only on `401 not_logged_in`. Today a `401 wrong_password` (change password, delete account) refreshes and resends the wrong password, so each typo counts twice toward the login limit | High |
| 3 | A 15-second time limit on app requests, so a bad connection shows a message instead of spinning | High |
| 4 | Change password screen (#34): save the new tokens right away | Medium |
| 5 | Forgot password screens (#5, #6): email, then 6-digit code and new password. Then turn the "forgot password" link back on | Medium |
| 6 | Show `pass_prediction_warning` (contract v0.8) and the "no listening" note on Home and the mock test result | Medium |
| 7 | Ask for notification permission, register the phone (#33), open Home when a reminder is tapped. Test in Expo Go on iPhone | Medium |
| 8 | Home map: split units by unit number, not position, so a missing unit never moves after a quiz | Low |

## Needs from the team

1. **Merge and load the mock tests** (#112 to #114, HP): after merging, the online database needs `load_quizzes` and `load_mock_tests`, not only units. Then I can test the full flow and open Session 2.
2. **Usage questions** (ANK): please check the wrong options in the mock test usage questions, and replace Session 1 mock #35 (same as Quiz 2 #39).
3. **Push notifications:** Expo Go on Android can't receive push. iPhone should work, but it needs the Expo project ID from the `padauk-lab` organization in `app.json`.

## Open questions

1. Set up ESLint for `frontend/`? `npm run lint` asks to install it. It would add packages and config files, so it should be its own PR (team)
2. `npm audit` reports 5 high warnings from Expo's tools (not code that ships to users). Leave them, or check later? (team)
3. Apple Developer membership: needed before TestFlight testing with people outside the team (team)
