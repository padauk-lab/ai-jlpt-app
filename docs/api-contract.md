# AI JLPT App, API Contract

Version: 0.5 (draft for team review)
Date: 2026-10-17
Changes in 0.2: removed #8 `GET /exam-dates`. The user picks any future exam date.
Changes in 0.3: decided how the study plan pace is calculated (#10).
Changes in 0.4: clarified #9 and #10 (score needed for N1 and N2, "today" is Japan time, `ai_tip_my` can be `null`).
Changes in 0.5: rate limits for log in and sign up (429 with a `Retry-After` header).
Owner: HP (Backend)
Reviewers: LMHP (Frontend), SWYH (AI), ANK (Data)

This file is the agreement between the app (frontend) and the server (backend).
It lists every request the app can make and exactly what the server sends back.
Frontend builds screens with these example responses as fake data. Backend builds
the server to return exactly these shapes. If anything here needs to change,
open a pull request and tell the team first.

## Contents

- [General rules](#general-rules)
- [Section 1: Onboarding (opening the app to the study plan)](#section-1-onboarding)
- [Section 2: Dashboard, sessions and units](#section-2-dashboard-sessions-and-units)
- [Section 3: Quiz and mock test](#section-3-quiz-and-mock-test)
- [Section 4: AI and settings](#section-4-ai-and-settings)
- [Endpoint summary](#endpoint-summary)
- [Open questions](#open-questions)

---

## General rules

### Base URL
All endpoints start with `/api/v1`. Example: `GET /api/v1/me`.
The `v1` lets us release a `v2` later without breaking older app versions.

### Scope
The app is for **JLPT N1 only**. App text is in **Burmese and Japanese only**.

### Login tokens
- After register or login, the server returns an `access_token` and a `refresh_token`.
- The app sends the access token with every request (except the ones marked "No login needed"):
  ```
  Authorization: Bearer <access_token>
  ```
- `access_token` lives about 15 minutes. `refresh_token` lives about 30 days.
- When the access token expires (error `401`), the app calls `POST /auth/refresh` quietly and retries.
- Tokens are stored in the phone's secure storage, never in plain storage.

### Data formats
- All requests and responses are JSON, UTF-8.
- Dates are `YYYY-MM-DD` (example `2026-12-06`). Date and time are ISO 8601 in UTC (example `2026-10-13T09:30:00Z`).
- IDs are whole numbers.
- Text fields ending in `_my` are Burmese, `_ja` are Japanese.
- **All explanations, meanings, notes, translations and AI answers are in Burmese.** Only the Japanese being learned (words, example sentences, questions, passages) is in Japanese.

### Japanese text with readings (furigana)
Any Japanese text that needs readings above the kanji uses a `ruby` list.
Each piece has the text, and a `reading` only if it contains kanji:
```json
"ruby": [
  { "text": "継続", "reading": "けいぞく" },
  { "text": "は" },
  { "text": "力", "reading": "ちから" },
  { "text": "なり" }
]
```
The app draws each `reading` above its `text`.

### Errors
Every error has the same shape:
```json
{
  "error": {
    "code": "validation_error",
    "message": "Score must be between 0 and 180.",
    "fields": { "last_score": "Must be between 0 and 180." }
  }
}
```
`fields` appears only for validation errors.

| Status | Meaning | When |
|---|---|---|
| 400 | Bad request | Invalid or expired link, wrong state (example: test already submitted) |
| 401 | Not logged in | Missing, invalid or expired token, wrong password |
| 403 | Forbidden | Item is locked, or belongs to another user |
| 404 | Not found | ID does not exist |
| 409 | Conflict | Email or username already used |
| 422 | Validation error | Input breaks a rule |
| 429 | Too many requests | Rate limit or daily AI limit reached |
| 500 | Server error | Our bug, the app shows a friendly message |

### Security rules (backend)
- The backend checks every rule itself. It never trusts the app alone.
- Passwords are stored only as secure hashes, never as plain text.
- Locked items return `403` even if the app is bypassed.
- Correct quiz and mock test answers are **never sent before the user answers**.
- Login, register, forgot password and AI endpoints are rate limited.
  - Log in: 5 wrong passwords per email in 15 minutes (a correct log in resets it), and 30 attempts per network in 5 minutes.
  - Sign up: 20 per network in 1 hour.
  - When a limit is hit: `429`, code `too_many_requests`, and a `Retry-After` header with the seconds to wait. The app shows a Burmese message and does not retry by itself.

---

## Section 1: Onboarding

Screens: Splash, Login, First-time setup, Generating plan, Study plan.

### 1. `GET /me`
Who is logged in, and is setup done? Used by the **Splash** screen to decide where to go.

Response `200`:
```json
{
  "id": 42,
  "email": "htet@example.com",
  "username": "htetpai",
  "login_method": "email",
  "onboarding_completed": true
}
```
- `login_method`: `"email"` or `"google"`.
- No token or expired: `401`, the app goes to Login.
- `onboarding_completed: false` goes to Setup. `true` goes to the Dashboard.

### 2. `POST /auth/register`
Create an account. **No login needed.**

Request:
```json
{
  "email": "htet@example.com",
  "username": "htetpai",
  "password": "my-strong-password"
}
```
Rules:
- `email`: valid email format.
- `username`: 3 to 20 characters, letters, numbers and underscore.
- `password`: at least 8 characters.

Response `201`:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "def50200a1...",
  "user": {
    "id": 42,
    "email": "htet@example.com",
    "username": "htetpai",
    "login_method": "email",
    "onboarding_completed": false
  }
}
```
Errors: `409` email or username already used, `422` rule broken.

### 3. `POST /auth/login`
Log in with email and password. **No login needed.**

Request:
```json
{ "email": "htet@example.com", "password": "my-strong-password" }
```
Response `200`: same as register.

Errors: `401` with message "Email or password is incorrect." It never says which one, so nobody can check which emails are registered.

### 4. `POST /auth/google`
Log in or sign up with Google. **No login needed.**
The app gets an ID token from Google sign-in and sends it here. The backend verifies it directly with Google.

Request:
```json
{ "id_token": "eyJhbGciOiJSUzI1NiIs..." }
```
Response `200`: same as register.
- First time: an account is created automatically. The username comes from the Google name and can be changed in Settings.

Errors: `401` invalid or expired Google token.

### 5. `POST /auth/forgot-password`
Send a password reset email. **No login needed.**

Request:
```json
{ "email": "htet@example.com" }
```
Response `200`, **always the same**, even if the email is not registered:
```json
{ "message": "If this email is registered, a reset link has been sent." }
```
- Limited to a few requests per hour per email and per device.

### 6. `POST /auth/reset-password`
Set a new password using the link from the email. **No login needed.**

Request:
```json
{ "reset_token": "token-from-email-link", "new_password": "my-new-password" }
```
Response `200`:
```json
{ "message": "Password updated. Please log in." }
```
- The link works once and expires after 1 hour.
- All existing logins for this user are signed out.

Errors: `400` link expired or already used, `422` password too short.

### 7. `POST /auth/refresh`
Get a new access token quietly. **No login needed** (uses the refresh token).

Request:
```json
{ "refresh_token": "def50200a1..." }
```
Response `200`:
```json
{ "access_token": "eyJhbGciOi...", "refresh_token": "a91f3c77b2..." }
```
- The old refresh token stops working after use.

Errors: `401` expired or invalid, the user must log in again.

### 8. Removed (was `GET /exam-dates`)
Removed in v0.2. There is no official date list. The user picks their own exam date in Setup (#9) and can change it in Settings (#29).
The number 8 is kept so the other endpoint numbers do not change.

### 9. `POST /onboarding`
Save the setup answers and create the study plan. Used by **First-time setup**, then the app shows **Generating plan** while waiting.

Request:
```json
{
  "last_level": "N2",
  "last_score": 112,
  "exam_date": "2026-12-06"
}
```
Rules:
- `last_level`: `"N1"`, `"N2"` or `"not_taken"`.
- `last_score`: whole number from 0 to 180. Needed for `"N1"` and `"N2"`. Must be `null` when `last_level` is `"not_taken"`.
- `exam_date`: any date after today (Japan time), or `null` for "Not decided yet".
  The app can show a hint: the JLPT is usually held on a Sunday in early July and early December.

Response `201`: the plan, same shape as #10.

Errors: `422` rule broken (the "Invalid input" message), `409` onboarding already done (use #29 in Settings instead).

### 10. `GET /plan`
The user's current study plan. Used by the **Study plan** screen.

Response `200`:
```json
{
  "exam_date": "2026-12-06",
  "days_left": 54,
  "units_total": 200,
  "units_done": 0,
  "units_per_day": 4,
  "finish_by": "2026-11-29",
  "ai_tip_my": "Burmese text: focus on reading practice on weekends.",
  "updated_at": "2026-10-13T09:30:00Z"
}
```
- The numbers are calculated by backend code. The AI only writes `ai_tip_my`.
- How: units left ÷ study days, rounded up, between 1 and 20 units per day. The last days before the exam stay free for review and mock tests: 7 days if the user already took N1, 14 days otherwise (never more than a third of the time left). Code: `backend/app/plan/calculator.py`.
- No exam date: `exam_date`, `days_left` and `finish_by` are `null`, and `units_per_day` is the default pace of 3.
- `ai_tip_my` is `null` until the AI tip is ready. The app hides the tip box when it is `null`.

Errors: `404` onboarding not done yet.

---

## Section 2: Dashboard, sessions and units

Screens: Dashboard, Session, Unit (Vocabulary and Grammar tabs), Saved words.
Bottom tabs: Home, Saved words, Settings.

Unlock rules (checked by the backend):
- Units unlock in order. A unit is done when the user taps "Mark as done".
- Quiz 1 unlocks after units 1 to 5. Quiz 2 unlocks after units 6 to 10.
- Units 6 to 10 unlock only after passing Quiz 1 (70% or more).
- The mock test unlocks after passing Quiz 2.
- The next session unlocks after the mock test is submitted (any score, no pass mark).

### 11. `GET /dashboard`
Everything the Dashboard needs in one call.

Response `200`:
```json
{
  "overall_progress": 32,
  "pass_prediction": 68,
  "today": { "units_done": 2, "units_goal": 4 },
  "continue": { "session_id": 3, "unit_id": 25, "label": "Session 3, Unit 5" },
  "sessions": [
    { "id": 1, "number": 1, "progress": 100, "status": "completed" },
    { "id": 2, "number": 2, "progress": 100, "status": "completed" },
    { "id": 3, "number": 3, "progress": 40, "status": "in_progress" },
    { "id": 4, "number": 4, "progress": 0, "status": "locked" }
  ]
}
```
- `overall_progress` and `progress`: 0 to 100.
- `pass_prediction`: 0 to 100, or `null` until the first mock test is done.
- `status`: `"completed"`, `"in_progress"`, `"available"` or `"locked"`.
- `sessions` always has all 20, in order.

### 12. `GET /proverbs/today`
Proverb of the day for the Dashboard card. Same proverb for everyone on the same day.

Response `200`:
```json
{
  "id": 7,
  "ruby": [
    { "text": "継続", "reading": "けいぞく" },
    { "text": "は" },
    { "text": "力", "reading": "ちから" },
    { "text": "なり" }
  ],
  "meaning_my": "Burmese translation.",
  "explanation_my": "Burmese explanation of when and why this proverb is used."
}
```
- Theme: effort, consistency, never giving up, not wasting time.

### 13. `GET /sessions/{id}`
The Session screen: units, quizzes and mock test.

Response `200`:
```json
{
  "id": 3,
  "number": 3,
  "units_done": 4,
  "units": [
    { "id": 21, "number": 1, "status": "completed" },
    { "id": 25, "number": 5, "status": "available" },
    { "id": 26, "number": 6, "status": "locked" }
  ],
  "quizzes": [
    { "id": 5, "covers_units": [1, 5], "status": "locked", "best_score": null },
    { "id": 6, "covers_units": [6, 10], "status": "locked", "best_score": null }
  ],
  "mock_test": { "id": 3, "status": "locked", "best_score": null, "last_score": null, "attempts": 0 }
}
```
- `units` always has all 10, in order. Unit `status`: `"completed"`, `"available"` or `"locked"`.
- Quiz `status`: `"locked"`, `"available"`, `"passed"` or `"failed"`. `best_score` is 0 to 100.
- Mock test `status`: `"locked"`, `"available"`, `"in_progress"` or `"completed"`. A completed mock test can be retaken.

Errors: `403` session locked.

### 14. `GET /units/{id}`
The Unit screen: 20 words and 1 grammar pattern.

Response `200`:
```json
{
  "id": 25,
  "session_number": 3,
  "number": 5,
  "status": "available",
  "words": [
    {
      "id": 501,
      "ruby": [{ "text": "意志力", "reading": "いしりょく" }],
      "meaning_my": "Burmese meaning.",
      "examples": [
        {
          "ruby": [
            { "text": "彼", "reading": "かれ" },
            { "text": "の" },
            { "text": "意志力", "reading": "いしりょく" },
            { "text": "はすごい。" }
          ],
          "translation_my": "Burmese translation."
        }
      ],
      "bookmarked": true
    }
  ],
  "grammar": {
    "id": 25,
    "pattern": "〜というよりも",
    "meaning_my": "Burmese meaning.",
    "how_to_use": "V/A/N (plain form) + というよりも",
    "how_to_use_my": "Burmese explanation of how and when to use this pattern.",
    "note_my": "Burmese note about a common mistake.",
    "examples": [
      {
        "ruby": [
          { "text": "彼", "reading": "かれ" },
          { "text": "は" },
          { "text": "面白", "reading": "おもしろ" },
          { "text": "いというよりも、" },
          { "text": "変", "reading": "へん" },
          { "text": "だ。" }
        ],
        "translation_my": "Burmese translation."
      }
    ]
  }
}
```
- `words` always has 20. Each word has 2 or 3 examples. Grammar has 2 or 3 examples.
- "More examples" button uses #27.

Errors: `403` unit locked.

### 15. `POST /units/{id}/complete`
"Mark as done". No request body.

Response `200`:
```json
{
  "unit_id": 25,
  "status": "completed",
  "next": { "type": "quiz", "id": 5 }
}
```
- `next.type`: `"unit"`, `"quiz"`, `"mock_test"` or `null`. Tells the app what to show next.
- Calling it again on a completed unit is safe and returns the same result.

Errors: `403` unit locked.

### 16. `GET /bookmarks`
Saved words list. Optional search: `GET /bookmarks?search=意志`.

Response `200`:
```json
{
  "total": 12,
  "words": [
    {
      "word_id": 501,
      "ruby": [{ "text": "意志力", "reading": "いしりょく" }],
      "meaning_my": "Burmese meaning.",
      "session_number": 3,
      "unit_number": 5,
      "saved_at": "2026-10-12T14:00:00Z"
    }
  ]
}
```
- Newest first.

### 17. `POST /bookmarks`
Save a word.

Request:
```json
{ "word_id": 501 }
```
Response `201`:
```json
{ "word_id": 501, "bookmarked": true }
```
- Saving an already saved word is safe and returns the same result.

Errors: `403` word is in a locked unit, `404` word not found.

### 18. `DELETE /bookmarks/{word_id}`
Remove a saved word. No request body.

Response `204` (no body).

Errors: `404` not bookmarked.

---

## Section 3: Quiz and mock test

Screens: Quiz, Quiz result, Mock test, Mock test result and review.

### Quiz rules
- 20 questions, a random mix of words and grammar from the 5 units it covers.
- Instant green or red feedback after each answer.
- Pass mark: 70%. Unlimited retakes. The best score counts.
- Every attempt is saved.

### Mock test rules
- JLPT N1 Language Knowledge format: 45 questions (vocabulary and grammar), plus 3 reading passages (short, medium, long).
- One continuous test. **Strict 30 minutes**, timed by the server (stored in the mock test template, so the team can change it).
- No feedback until submitted.
- If the app closes, the user can resume while time remains. The clock keeps running.
- At 0, the server submits automatically with the answers saved so far.
- **No pass mark.** Any score unlocks the next session. The mock test measures readiness and feeds the dashboard's pass prediction.
- **Retakes allowed** any time after the first attempt, for review. Each retake uses the same questions.
- **Only the first attempt** of each mock test counts toward the pass prediction. Retakes do not change it, because the questions are already known.
- To get a new prediction, the user resets all progress in Settings (#37) and goes through every session, quiz and mock test again. After a reset, the first attempt of each mock test counts again.

### 19. `POST /quizzes/{id}/attempts`
Start a quiz. No request body.

Response `201`:
```json
{
  "attempt_id": 880,
  "quiz_id": 5,
  "total_questions": 20,
  "questions": [
    {
      "id": 3101,
      "number": 1,
      "type": "kanji_reading",
      "prompt_ruby": [
        { "text": "彼の" },
        { "text": "意志力" },
        { "text": "には驚かされる。" }
      ],
      "underline": "意志力",
      "options": [
        { "id": "a", "text": "いしりょく" },
        { "id": "b", "text": "いしりき" },
        { "id": "c", "text": "いしょく" },
        { "id": "d", "text": "いじりょく" }
      ]
    }
  ]
}
```
- **No correct answers are included.**
- `underline`: optional, the part of the prompt being tested.

Errors: `403` quiz locked.

### 20. `POST /quiz-attempts/{id}/answers`
Answer one question and get instant feedback.

Request:
```json
{ "question_id": 3101, "selected_option_id": "b" }
```
Response `200`:
```json
{
  "question_id": 3101,
  "is_correct": false,
  "selected_option_id": "b",
  "correct_option_id": "a",
  "answered": 1,
  "correct_so_far": 0
}
```
- The "Why?" button uses #28 with this `question_id` and `selected_option_id`.
- A question can be answered only once per attempt.

Errors: `400` already answered or attempt finished, `403` not your attempt.

### 21. `POST /quiz-attempts/{id}/finish`
Finish the quiz. Unanswered questions count as wrong. No request body.

Response `200`:
```json
{
  "attempt_id": 880,
  "score": 75,
  "correct": 15,
  "total": 20,
  "passed": true,
  "pass_mark": 70,
  "best_score": 75,
  "wrong_questions": [3104, 3109, 3112, 3115, 3120]
}
```
- `score`, `pass_mark` and `best_score` are percentages.

### 22. `GET /quiz-attempts/{id}`
Review a finished quiz: every question with the user's answer and the correct answer.

Response `200`:
```json
{
  "attempt_id": 880,
  "score": 75,
  "passed": true,
  "finished_at": "2026-10-13T10:10:00Z",
  "questions": [
    {
      "id": 3101,
      "number": 1,
      "prompt_ruby": [{ "text": "彼の意志力には驚かされる。" }],
      "options": [
        { "id": "a", "text": "いしりょく" },
        { "id": "b", "text": "いしりき" },
        { "id": "c", "text": "いしょく" },
        { "id": "d", "text": "いじりょく" }
      ],
      "selected_option_id": "b",
      "correct_option_id": "a",
      "is_correct": false
    }
  ]
}
```
Errors: `400` attempt not finished yet, `403` not your attempt.

### 23. `POST /mock-tests/{id}/attempts`
Start the mock test, **resume** the one in progress, or start a **retake** after a finished one. No request body.

Response `201` (new) or `200` (resumed):
```json
{
  "attempt_id": 410,
  "mock_test_id": 3,
  "started_at": "2026-10-13T11:00:00Z",
  "ends_at": "2026-10-13T11:30:00Z",
  "server_time": "2026-10-13T11:00:00Z",
  "sections": [
    {
      "part": "language_knowledge",
      "questions": [
        {
          "id": 9001,
          "number": 1,
          "type": "kanji_reading",
          "prompt_ruby": [{ "text": "..." }],
          "options": [
            { "id": "a", "text": "..." },
            { "id": "b", "text": "..." },
            { "id": "c", "text": "..." },
            { "id": "d", "text": "..." }
          ]
        }
      ]
    },
    {
      "part": "reading",
      "passages": [
        {
          "id": 71,
          "length": "short",
          "text_ruby": [{ "text": "..." }],
          "questions": [
            {
              "id": 9046,
              "number": 46,
              "prompt_ruby": [{ "text": "..." }],
              "options": [
                { "id": "a", "text": "..." },
                { "id": "b", "text": "..." },
                { "id": "c", "text": "..." },
                { "id": "d", "text": "..." }
              ]
            }
          ]
        }
      ]
    }
  ],
  "saved_answers": { "9001": "c" }
}
```
- The app shows a countdown using `ends_at` and `server_time`, so the phone clock does not matter.
- `saved_answers` restores answers when resuming.
- `language_knowledge` has 45 questions. `reading` has 3 passages: `"short"`, `"medium"`, `"long"`.
- **No correct answers are included.**

Errors: `403` mock test locked.

### 24. `PUT /mock-attempts/{id}/answers`
Save or change one answer. No feedback.

Request:
```json
{ "question_id": 9001, "selected_option_id": "c" }
```
Response `200`:
```json
{ "question_id": 9001, "saved": true, "answered_count": 12, "total_questions": 51 }
```
Errors: `400` time is up or already submitted (the app then opens the result), `403` not your attempt.

### 25. `POST /mock-attempts/{id}/submit`
Submit before time runs out. No request body. If time runs out, the server submits automatically.

Response `200`: same as #26.

Errors: `400` already submitted.

### 26. `GET /mock-attempts/{id}/result`
The Mock test result and review screen.

Response `200`:
```json
{
  "attempt_id": 410,
  "submitted_at": "2026-10-13T11:27:40Z",
  "submitted_by": "user",
  "time_used_seconds": 1660,
  "time_limit_seconds": 1800,
  "score": { "correct": 38, "total": 51, "percent": 75 },
  "parts": [
    { "part": "vocabulary", "correct": 22, "total": 25 },
    { "part": "grammar", "correct": 12, "total": 20 },
    { "part": "reading", "correct": 4, "total": 6 }
  ],
  "pass_prediction": 70,
  "counts_for_prediction": true,
  "questions": [
    {
      "id": 9001,
      "number": 1,
      "part": "vocabulary",
      "prompt_ruby": [{ "text": "..." }],
      "options": [
        { "id": "a", "text": "..." },
        { "id": "b", "text": "..." },
        { "id": "c", "text": "..." },
        { "id": "d", "text": "..." }
      ],
      "selected_option_id": "c",
      "correct_option_id": "a",
      "is_correct": false
    }
  ]
}
```
- `submitted_by`: `"user"` or `"timeout"`.
- `counts_for_prediction`: `true` for the first attempt (in the current round), `false` for retakes. When `false`, `pass_prediction` shows the current value unchanged.
- Unanswered questions have `selected_option_id: null`.
- The "Why?" button on each question uses #28.
- Part totals depend on the template. The numbers above are an example.

Errors: `400` not submitted yet, `403` not your attempt.

---

## Section 4: AI and settings

### AI rules
- AI is used only through 2 buttons. There is no free chat.
  - **More examples**: on word and grammar cards.
  - **Why?**: in quiz feedback, quiz review and mock test review.
- The app sends only IDs. The backend looks up the real content in the database and gives it to the AI, so the AI always works from our checked data.
- AI replies are in Burmese, written by a patient, professional Japanese teacher, with simple examples and analogies.
- "Why?" explanations are saved after the first time and reused for everyone. ANK can review and correct them.
- "More examples" has a daily limit per user (default 50, a server setting). The app shows the remaining count only when 5 or fewer are left.

### 27. `POST /ai/examples`
"More examples" button. Generates new example sentences.

Request:
```json
{ "item_type": "word", "item_id": 501 }
```
- `item_type`: `"word"` or `"grammar"`.

Response `200`:
```json
{
  "item_type": "word",
  "item_id": 501,
  "examples": [
    {
      "ruby": [{ "text": "..." }],
      "translation_my": "Burmese translation."
    }
  ],
  "remaining_today": 47
}
```
- Returns 3 new examples.

Errors: `403` item is in a locked unit, `429` daily limit reached, `503` AI service temporarily unavailable (the app shows "Try again later").

### 28. `POST /ai/explain`
"Why?" button. Explains why the correct answer is right, and why the selected answer is wrong.

Request:
```json
{ "question_id": 3101, "selected_option_id": "b" }
```
Response `200`:
```json
{
  "question_id": 3101,
  "correct_option_id": "a",
  "why_correct_my": "Burmese explanation of why (a) is correct.",
  "why_selected_wrong_my": "Burmese explanation of why (b) is wrong.",
  "other_options_my": {
    "c": "Burmese note on (c).",
    "d": "Burmese note on (d)."
  }
}
```
- `why_selected_wrong_my` is `null` when the selected answer was correct.
- Works only for questions the user has already answered (quiz) or submitted (mock test). Otherwise `403`, so nobody can use it to get answers early. Questions skipped in a finished quiz also work, because the review (#22) already shows their answers.
- Answers are saved per question and choice and shared by all users, so only the first request waits for the AI.

Errors: `403` not answered yet, `404` question not found, `503` AI service temporarily unavailable.

### Settings screen groups
Profile, Study setup, Notifications, Account, About.

### 29. `PUT /me/study-settings`
Change last level, score or exam date. **Recalculates the study plan.** The app shows a warning first.

Request: same as #9.

Response `200`: the new plan, same shape as #10.

Errors: `422` rule broken.

### 30. `PUT /me`
Change the username.

Request:
```json
{ "username": "htet_pai" }
```
Response `200`: same shape as #1.

Errors: `409` username taken, `422` rule broken.

### 31. `GET /me/notifications`
Current notification settings.

Response `200`:
```json
{
  "daily_reminder": true,
  "reminder_time": "20:00",
  "proverb_notification": true,
  "timezone": "Asia/Tokyo"
}
```

### 32. `PUT /me/notifications`
Change notification settings.

Request: same shape as #31.

Response `200`: same shape as #31.

Errors: `422` invalid time or timezone.

### 33. `POST /me/devices`
Register this phone for push notifications. The app calls it after the user allows notifications, and again if the push token changes.

Request:
```json
{ "push_token": "ExponentPushToken[xxxxxxxx]", "platform": "ios" }
```
- `platform`: `"ios"`, `"android"` or `"web"`.

Response `201`:
```json
{ "registered": true }
```

### 34. `POST /auth/change-password`
Change password. Only for email users (Google users have no password here).

Request:
```json
{ "current_password": "my-strong-password", "new_password": "my-new-password" }
```
Response `200`:
```json
{ "message": "Password updated." }
```
- Other devices are signed out.

Errors: `401` current password wrong, `400` Google account, `422` new password too short.

### 35. `POST /auth/logout`
Log out on this device.

Request:
```json
{ "refresh_token": "def50200a1..." }
```
Response `204` (no body).
- The refresh token is cancelled. The app also deletes the tokens from secure storage.

### 36. `DELETE /me`
Delete the account and all its data (required by the App Store).

Request:
```json
{ "confirm": "DELETE", "password": "my-strong-password" }
```
- `password` is required for email users. Google users send only `confirm`.

Response `204` (no body).

Errors: `401` wrong password, `422` missing confirmation.

### 37. `POST /me/reset-progress`
"Reset all progress" in Settings. Starts a new round from Session 1. The app shows a strong warning first.

Request:
```json
{ "confirm": "RESET" }
```
Response `200`:
```json
{
  "round": 2,
  "plan": { "...": "same shape as #10" }
}
```
- **Clears**: units done, quiz results, mock test results, pass prediction. Sessions lock again from Session 2.
- **Keeps**: account, settings, saved words.
- **Recalculates** the study plan from today.
- Old results are archived, not deleted, so past rounds can be shown later.
- After a reset, the first attempt of each mock test counts toward the prediction again.

Errors: `422` missing confirmation.

---

## Endpoint summary

| # | Method | Path | Section | Login needed |
|---|---|---|---|---|
| 1 | GET | `/me` | 1 | Yes |
| 2 | POST | `/auth/register` | 1 | No |
| 3 | POST | `/auth/login` | 1 | No |
| 4 | POST | `/auth/google` | 1 | No |
| 5 | POST | `/auth/forgot-password` | 1 | No |
| 6 | POST | `/auth/reset-password` | 1 | No |
| 7 | POST | `/auth/refresh` | 1 | No (refresh token) |
| 8 | | Removed in v0.2 | 1 | |
| 9 | POST | `/onboarding` | 1 | Yes |
| 10 | GET | `/plan` | 1 | Yes |
| 11 | GET | `/dashboard` | 2 | Yes |
| 12 | GET | `/proverbs/today` | 2 | Yes |
| 13 | GET | `/sessions/{id}` | 2 | Yes |
| 14 | GET | `/units/{id}` | 2 | Yes |
| 15 | POST | `/units/{id}/complete` | 2 | Yes |
| 16 | GET | `/bookmarks` | 2 | Yes |
| 17 | POST | `/bookmarks` | 2 | Yes |
| 18 | DELETE | `/bookmarks/{word_id}` | 2 | Yes |
| 19 | POST | `/quizzes/{id}/attempts` | 3 | Yes |
| 20 | POST | `/quiz-attempts/{id}/answers` | 3 | Yes |
| 21 | POST | `/quiz-attempts/{id}/finish` | 3 | Yes |
| 22 | GET | `/quiz-attempts/{id}` | 3 | Yes |
| 23 | POST | `/mock-tests/{id}/attempts` | 3 | Yes |
| 24 | PUT | `/mock-attempts/{id}/answers` | 3 | Yes |
| 25 | POST | `/mock-attempts/{id}/submit` | 3 | Yes |
| 26 | GET | `/mock-attempts/{id}/result` | 3 | Yes |
| 27 | POST | `/ai/examples` | 4 | Yes |
| 28 | POST | `/ai/explain` | 4 | Yes |
| 29 | PUT | `/me/study-settings` | 4 | Yes |
| 30 | PUT | `/me` | 4 | Yes |
| 31 | GET | `/me/notifications` | 4 | Yes |
| 32 | PUT | `/me/notifications` | 4 | Yes |
| 33 | POST | `/me/devices` | 4 | Yes |
| 34 | POST | `/auth/change-password` | 4 | Yes |
| 35 | POST | `/auth/logout` | 4 | Yes |
| 36 | DELETE | `/me` | 4 | Yes |
| 37 | POST | `/me/reset-progress` | 4 | Yes |

---

## Open questions

1. **Pass prediction formula**: how mock test scores turn into a 0 to 100 prediction. HP and ANK to propose.
2. **Mock test part split**: exact number of vocabulary, grammar and reading questions per template. ANK to confirm against the official N1 format.
3. **Plan pace by level**: decided in v0.3, see #10. The score does not change the pace yet; we tune it after real users try it.
4. **LLM choice**: which AI model to use. SWYH to propose.
5. **Daily AI limit**: is 50 "More examples" per day right? Team to decide after testing.
