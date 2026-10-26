# Database design

Version: 0.2 (draft for team review)
Date: 2026-10-13
Owner: HP (Backend). ANK takes over after Dec 6.
Based on: `docs/api-contract.md` v0.2
Changes in 0.2: removed the `exam_dates` table (the user picks any future exam date).

This file describes every table in the PostgreSQL database, its columns, and how tables connect.
Backend code (SQLAlchemy models and Alembic migrations) must match this file.
If a table or column needs to change, update this file in the same pull request.

## Contents

- [General rules](#general-rules)
- [Overview](#overview)
- [Group 1: Users and login](#group-1-users-and-login)
- [Group 2: Study setup and plan](#group-2-study-setup-and-plan)
- [Group 3: Learning content](#group-3-learning-content)
- [Group 4: Quizzes and mock tests](#group-4-quizzes-and-mock-tests)
- [Group 5: User progress and AI](#group-5-user-progress-and-ai)
- [Rounds and reset progress](#rounds-and-reset-progress)
- [Values calculated, not stored](#values-calculated-not-stored)
- [Open questions](#open-questions)

---

## General rules

### Naming
- Table and column names: lowercase `snake_case`. Tables are plural (`users`, `words`).
- Every table has `id` as its primary key (auto-increment `bigint`), unless noted (some tables use two columns as their key).
- Links to other tables end in `_id` (example: `unit_id` points to `units.id`). These are **foreign keys**.

### Types
- Text: `text`. Short fixed choices (like `"email"` or `"google"`) are `text` with a `CHECK` rule listing the allowed values.
- Japanese text with readings above kanji (`ruby` in the contract) is stored as `jsonb`, exactly as the contract shapes it.
- Dates: `date`. Date and time: `timestamptz`, always stored in UTC.
- True or false: `boolean`.

### Common columns
- `created_at timestamptz NOT NULL DEFAULT now()` on every table.
- `updated_at timestamptz` on tables whose rows change.

### Deleting
- **User data** uses `ON DELETE CASCADE`: deleting a user (endpoint #36) deletes all their rows.
- **Content** uses `ON DELETE RESTRICT`: a unit cannot be deleted while words still point to it, so content is never lost by accident.

### Indexes
- Every foreign key column has an index, so lookups stay fast.
- Unique rules are listed per table.

### Security
- Passwords are stored only as a slow, salted hash (Argon2 or bcrypt). Never the password itself.
- Refresh tokens and password reset tokens are stored only as hashes. The real token exists only in the app or the email link.
- Correct answers live in `questions.correct_option_id` and are never sent to the app before the user answers (rule from the contract).

---

## Overview

26 tables in 5 groups.

```
USERS AND LOGIN               STUDY SETUP AND PLAN
users                         study_settings   (1 per user)
 ├── refresh_tokens            plans            (1 per user)
 ├── password_reset_tokens
 ├── devices
 ├── notification_settings
 └── notification_log

LEARNING CONTENT (same for everyone)
sessions (10)
 ├── units (10 each)
 │    ├── words (20 each) ── examples
 │    └── grammar (1 each) ── examples
 ├── quizzes (2 each) ── questions
 └── mock_tests (1 each)
      ├── questions
      └── reading_passages (3) ── questions
proverbs

USER PROGRESS AND AI
unit_progress        (user + unit)
bookmarks            (user + word)
quiz_attempts        (user + quiz)  ── quiz_attempt_questions, quiz_answers
mock_attempts        (user + mock test) ── mock_answers
ai_explanations      (question + option, shared by all users)
ai_usage             (user + day)
```

Kinds of links:
- **One to one**: a user has one `study_settings` row and one `plans` row.
- **One to many**: a session has many units, a unit has many words.
- **Many to many**: users and words, through `bookmarks`.

---

## Group 1: Users and login

### `users`
One row per account.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| email | text | NOT NULL, unique (lowercase) | Stored lowercase so `Htet@x.com` and `htet@x.com` are the same |
| username | text | NOT NULL, unique (lowercase), 3 to 20 chars | Letters, numbers, underscore |
| password_hash | text | nullable | Empty for Google-only users |
| google_sub | text | nullable, unique | Google's permanent user ID |
| login_method | text | NOT NULL, `email` or `google` | |
| onboarding_completed | boolean | NOT NULL, default false | |
| current_round | integer | NOT NULL, default 1 | Goes up by 1 on each reset (#37) |
| created_at | timestamptz | NOT NULL | |
| updated_at | timestamptz | | |

Rule: `password_hash` or `google_sub` must be set (at least one).

### `refresh_tokens`
"Stay logged in" tokens. Lets us sign out a device (#35) or all devices (#6, #34).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| user_id | bigint | NOT NULL, → users, cascade | |
| token_hash | text | NOT NULL, unique | Hash of the token, never the token |
| expires_at | timestamptz | NOT NULL | About 30 days |
| revoked_at | timestamptz | nullable | Set when used, logged out or cancelled |
| created_at | timestamptz | NOT NULL | |

### `password_reset_tokens`
One-time links from "Forgot password" (#5, #6).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| user_id | bigint | NOT NULL, → users, cascade | |
| token_hash | text | NOT NULL, unique | |
| expires_at | timestamptz | NOT NULL | 1 hour |
| used_at | timestamptz | nullable | Works only once |
| created_at | timestamptz | NOT NULL | |

### `devices`
Phones registered for push notifications (#33).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| user_id | bigint | NOT NULL, → users, cascade | |
| push_token | text | NOT NULL, unique | |
| platform | text | NOT NULL, `ios`, `android` or `web` | |
| last_seen_at | timestamptz | | |
| created_at | timestamptz | NOT NULL | |

### `notification_settings`
One row per user (#31, #32).

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | primary key, → users, cascade | |
| daily_reminder | boolean | NOT NULL, default true | |
| reminder_time | time | NOT NULL, default 20:00 | Local time of the user |
| proverb_notification | boolean | NOT NULL, default true | |
| timezone | text | NOT NULL, default `Asia/Tokyo` | IANA name |
| updated_at | timestamptz | | |

### `notification_log`
Notifications already sent, so each one goes out at most once per user per day, even with two servers.
Rows older than 7 days are deleted automatically.

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | primary key (with kind, local_date), → users, cascade | |
| kind | text | primary key, `daily_reminder` | More kinds later (Proverb of the day) |
| local_date | date | primary key | The day in the user's own timezone |
| sent_at | timestamptz | NOT NULL | |

---

## Group 2: Study setup and plan

### `study_settings`
The onboarding answers (#9), changeable in Settings (#29). One row per user.

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | primary key, → users, cascade | |
| last_level | text | NOT NULL, `N1`, `N2` or `not_taken` | |
| last_score | smallint | nullable, 0 to 180 | Must be empty when `last_level` is `not_taken` |
| exam_date | date | nullable | Empty means "not decided yet". The backend checks it is after today when saved |
| updated_at | timestamptz | | |

### `plans`
The study plan (#10). One row per user, recalculated on onboarding, settings change and reset.

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | primary key, → users, cascade | |
| units_per_day | smallint | NOT NULL, at least 1 | Default pace 3 when no exam date |
| finish_by | date | nullable | Empty when no exam date |
| ai_tip_my | text | | Burmese tip from the AI |
| updated_at | timestamptz | NOT NULL | |

---

## Group 3: Learning content

Prepared by ANK, loaded from `data/`. Same for every user.

### `sessions`

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| number | smallint | NOT NULL, unique, 1 to 20 | The app uses 1 to 10 (content rules refuse session 11 and later) |

### `units`

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| session_id | bigint | NOT NULL, → sessions, restrict | |
| number | smallint | NOT NULL, 1 to 10 | |

Unique: (`session_id`, `number`).

### `words`
20 per unit.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| unit_id | bigint | NOT NULL, → units, restrict | |
| position | smallint | NOT NULL, 1 to 20 | Order in the unit |
| word | text | NOT NULL | Plain text, for search (example: 意志力) |
| furigana | text | NOT NULL | How to read it, for search (example: いしりょく) |
| ruby | jsonb | NOT NULL | Contract's ruby format, for display |
| meaning_my | text | NOT NULL | Burmese meaning |

Unique: (`unit_id`, `position`).

### `grammar`
1 per unit.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| unit_id | bigint | NOT NULL, unique, → units, restrict | Unique means 1 per unit |
| pattern | text | NOT NULL | Example: 〜というよりも |
| meaning_my | text | NOT NULL | |
| how_to_use | text | NOT NULL | Pattern formula |
| how_to_use_my | text | NOT NULL | Burmese explanation |
| note_my | text | | Common mistake |

### `examples`
Example sentences for words and grammar (2 to 3 each).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| word_id | bigint | nullable, → words, restrict | |
| grammar_id | bigint | nullable, → grammar, restrict | |
| position | smallint | NOT NULL | |
| ruby | jsonb | NOT NULL | Japanese sentence |
| translation_my | text | NOT NULL | Burmese translation |

Rule: exactly one of `word_id` or `grammar_id` is set.
AI "More examples" (#27) are generated fresh and **not** stored here.

### `proverbs`
Proverb of the day (#12).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| ruby | jsonb | NOT NULL | |
| meaning_my | text | NOT NULL | |
| explanation_my | text | NOT NULL | |
| is_active | boolean | NOT NULL, default true | |

---

## Group 4: Quizzes and mock tests

### `quizzes`
2 per session (units 1 to 5, units 6 to 10).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| session_id | bigint | NOT NULL, → sessions, restrict | |
| number | smallint | NOT NULL, 1 or 2 | |
| first_unit | smallint | NOT NULL | 1 or 6 |
| last_unit | smallint | NOT NULL | 5 or 10 |
| question_count | smallint | NOT NULL, default 20 | Questions per attempt |
| pass_mark | smallint | NOT NULL, default 70 | Percent |

Unique: (`session_id`, `number`).
Each quiz has a **question bank** (more than 20 questions). Each attempt picks 20 at random.

### `mock_tests`
1 per session.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| session_id | bigint | NOT NULL, unique, → sessions, restrict | |
| time_limit_seconds | integer | NOT NULL, default 1800 | 30 minutes, changeable here |

### `reading_passages`
3 per mock test.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| mock_test_id | bigint | NOT NULL, → mock_tests, restrict | |
| length | text | NOT NULL, `short`, `medium` or `long` | |
| position | smallint | NOT NULL | Order in the test |
| text_ruby | jsonb | NOT NULL | The passage |

Unique: (`mock_test_id`, `length`).

### `questions`
Every quiz and mock test question.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| quiz_id | bigint | nullable, → quizzes, restrict | Set for quiz questions |
| mock_test_id | bigint | nullable, → mock_tests, restrict | Set for mock test questions |
| passage_id | bigint | nullable, → reading_passages, restrict | Set for reading questions |
| part | text | NOT NULL, `vocabulary`, `grammar` or `reading` | |
| type | text | NOT NULL | Example: `kanji_reading`, `paraphrase` |
| number | smallint | | Mock test: order in the test. Quiz: the question's number in its bank file, used to update it safely (attempt order is random) |
| prompt_ruby | jsonb | NOT NULL | |
| underline | text | nullable | Part of the prompt being tested |
| options | jsonb | NOT NULL | `[{"id":"a","text":"..."}]`, 4 options |
| correct_option_id | text | NOT NULL, `a` to `d` | **Never sent before answering** |
| word_id | bigint | nullable, → words | Which word it tests, for review |
| grammar_id | bigint | nullable, → grammar | Which grammar it tests |

Rule: exactly one of `quiz_id` or `mock_test_id` is set.

---

## Group 5: User progress and AI

All progress tables have a `round` column. See [Rounds and reset progress](#rounds-and-reset-progress).

### `unit_progress`
Units marked as done (#15).

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | → users, cascade | |
| unit_id | bigint | → units, restrict | |
| round | integer | | |
| completed_at | timestamptz | NOT NULL | |

Primary key: (`user_id`, `unit_id`, `round`).

### `bookmarks`
Saved words (#16 to #18). Not affected by reset.

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | → users, cascade | |
| word_id | bigint | → words, restrict | |
| created_at | timestamptz | NOT NULL | |

Primary key: (`user_id`, `word_id`).

### `quiz_attempts`
Each time a user takes a quiz (#19, #21, #22).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| user_id | bigint | NOT NULL, → users, cascade | |
| quiz_id | bigint | NOT NULL, → quizzes, restrict | |
| round | integer | NOT NULL | |
| started_at | timestamptz | NOT NULL | |
| finished_at | timestamptz | nullable | Empty while in progress |
| correct | smallint | nullable | |
| score | smallint | nullable, 0 to 100 | Percent |
| passed | boolean | nullable | |

Index: (`user_id`, `quiz_id`, `round`).

### `quiz_attempt_questions`
The 20 questions picked for one attempt, in order.

| Column | Type | Rules | Notes |
|---|---|---|---|
| attempt_id | bigint | → quiz_attempts, cascade | |
| question_id | bigint | → questions, restrict | |
| position | smallint | NOT NULL, 1 to 20 | |

Primary key: (`attempt_id`, `question_id`).

### `quiz_answers`
One answer per question per attempt (#20).

| Column | Type | Rules | Notes |
|---|---|---|---|
| attempt_id | bigint | → quiz_attempts, cascade | |
| question_id | bigint | → questions, restrict | |
| selected_option_id | text | NOT NULL, `a` to `d` | |
| is_correct | boolean | NOT NULL | |
| answered_at | timestamptz | NOT NULL | |

Primary key: (`attempt_id`, `question_id`). This also makes "answer only once" automatic.

### `mock_attempts`
Each time a user takes a mock test (#23 to #26).

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| user_id | bigint | NOT NULL, → users, cascade | |
| mock_test_id | bigint | NOT NULL, → mock_tests, restrict | |
| round | integer | NOT NULL | |
| started_at | timestamptz | NOT NULL | |
| ends_at | timestamptz | NOT NULL | `started_at` + time limit, set by the server |
| submitted_at | timestamptz | nullable | Empty while in progress |
| submitted_by | text | nullable, `user` or `timeout` | |
| correct | smallint | nullable | |
| total | smallint | nullable | |
| counts_for_prediction | boolean | NOT NULL | True only for the first attempt in a round |

Rules:
- Only one attempt **in progress** per user and mock test (unique where `submitted_at` is empty).
- A background job submits attempts whose `ends_at` has passed.

### `mock_answers`
Saved answers, changeable until submitted (#24).

| Column | Type | Rules | Notes |
|---|---|---|---|
| attempt_id | bigint | → mock_attempts, cascade | |
| question_id | bigint | → questions, restrict | |
| selected_option_id | text | NOT NULL, `a` to `d` | |
| updated_at | timestamptz | NOT NULL | |

Primary key: (`attempt_id`, `question_id`).
`is_correct` is worked out at submit time, not while the test is running.

### `ai_explanations`
Saved "Why?" answers (#28), reused for everyone. ANK can review and correct them.

| Column | Type | Rules | Notes |
|---|---|---|---|
| id | bigint | primary key | |
| question_id | bigint | NOT NULL, → questions, cascade | |
| selected_option_id | text | NOT NULL, `a` to `d` | The answer the user picked |
| why_correct_my | text | NOT NULL | |
| why_selected_wrong_my | text | nullable | Empty when the selected answer was correct |
| other_options_my | jsonb | | `{"c": "...", "d": "..."}` |
| model | text | NOT NULL | Which AI model wrote it |
| reviewed_at | timestamptz | nullable | Set when ANK checks it |
| created_at | timestamptz | NOT NULL | |

Unique: (`question_id`, `selected_option_id`). One saved explanation per answer choice.

### `ai_usage`
Daily "More examples" count per user (#27).

| Column | Type | Rules | Notes |
|---|---|---|---|
| user_id | bigint | → users, cascade | |
| usage_date | date | | In the user's timezone |
| examples_count | integer | NOT NULL, default 0 | |

Primary key: (`user_id`, `usage_date`).

---

## Rounds and reset progress

- `users.current_round` starts at 1.
- Every progress row (`unit_progress`, `quiz_attempts`, `mock_attempts`) saves the round it belongs to.
- The app only looks at rows where `round` equals the user's `current_round`.
- **Reset all progress** (#37) adds 1 to `current_round`. Nothing is deleted, so old rounds stay as history ("Round 1: 62%, Round 2: 78%").
- `bookmarks`, settings and the account are not tied to rounds, so reset keeps them.

---

## Values calculated, not stored

These are worked out when needed, so they can never be out of date:

| Value | How |
|---|---|
| `days_left` | `exam_date` minus today |
| `units_done`, `overall_progress` | Count of `unit_progress` rows in the current round |
| Unit, quiz, session, mock test `status` (locked, available...) | From `unit_progress`, best quiz score and submitted mock attempts in the current round |
| Quiz `best_score` | Highest `quiz_attempts.score` in the current round |
| Today's goal | Units completed today vs `plans.units_per_day` |
| Pass prediction | From `mock_attempts` where `counts_for_prediction` is true, in the current round (formula still open) |
| Proverb of the day | Picked from active proverbs by today's date, same for everyone |

---

## Open questions

1. **Pass prediction formula** (HP and ANK).
2. **Mock test question split**: vocabulary, grammar and reading counts per test (ANK).
3. **Quiz bank size**: how many questions per quiz bank, so retakes get a different mix (ANK, suggestion: 40).
4. **Old AI explanations**: when content is corrected, should saved explanations for that question be deleted and regenerated? (HP and SWYH, suggestion: yes).
