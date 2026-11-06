// Response shapes from docs/api-contract.md. Field names match the contract exactly.
import type { RubyPiece } from '@/components/RubyText';

export type SessionStatus = 'completed' | 'in_progress' | 'available' | 'locked';
export type UnitStatus = 'completed' | 'available' | 'locked';
export type QuizStatus = 'locked' | 'available' | 'passed' | 'failed';
export type MockTestStatus = 'locked' | 'available' | 'in_progress' | 'completed';

// #11 GET /dashboard
export type Dashboard = {
  overall_progress: number;
  pass_prediction: number | null;
  today: { units_done: number; units_goal: number };
  continue: { session_id: number; unit_id: number; label: string } | null;
  // id is null while a session's content isn't loaded yet (contract v0.6)
  sessions: { id: number | null; number: number; progress: number; status: SessionStatus }[];
};

// #12 GET /proverbs/today
export type Proverb = {
  id: number;
  ruby: RubyPiece[];
  meaning_my: string;
  explanation_my: string;
};

// #13 GET /sessions/{id}. While content is still being added, a session can have
// fewer than 10 units, no quizzes, and no mock test.
export type SessionDetail = {
  id: number;
  number: number;
  units_done: number;
  units: { id: number; number: number; status: UnitStatus }[];
  quizzes: {
    id: number;
    covers_units: [number, number];
    status: QuizStatus;
    best_score: number | null;
  }[];
  // null while the session has no mock test yet (contract #13)
  mock_test: {
    id: number;
    status: MockTestStatus;
    best_score: number | null;
    last_score: number | null;
    attempts: number;
  } | null;
};

export type Example = {
  ruby: RubyPiece[];
  translation_my: string;
};

// #14 GET /units/{id}
export type Word = {
  id: number;
  ruby: RubyPiece[];
  meaning_my: string;
  examples: Example[];
  bookmarked: boolean;
  // Proposed, NOT in the contract yet (open decision #8). Shown only when present.
  meaning_ja?: string;
  definition_my?: string;
};

export type Grammar = {
  id: number;
  pattern: string;
  meaning_my: string;
  how_to_use: string;
  how_to_use_my: string;
  note_my: string;
  examples: Example[];
};

export type UnitDetail = {
  id: number;
  session_number: number;
  number: number;
  status: UnitStatus;
  words: Word[];
  grammar: Grammar | null; // the backend sends null while a unit's grammar isn't loaded
};

// #15 POST /units/{id}/complete
export type UnitCompleteResult = {
  unit_id: number;
  status: 'completed';
  next: { type: 'unit' | 'quiz' | 'mock_test'; id: number } | null;
};

// #19 POST /quizzes/{id}/attempts
export type QuizOption = { id: 'a' | 'b' | 'c' | 'd'; text: string };

export type QuizQuestion = {
  id: number;
  number: number;
  type: string;
  prompt_ruby: RubyPiece[];
  underline?: string;
  options: QuizOption[];
};

export type QuizAttempt = {
  attempt_id: number;
  quiz_id: number;
  total_questions: number;
  questions: QuizQuestion[];
};

// #20 POST /quiz-attempts/{id}/answers
export type AnswerResult = {
  question_id: number;
  is_correct: boolean;
  selected_option_id: QuizOption['id'];
  correct_option_id: QuizOption['id'];
  answered: number;
  correct_so_far: number;
};

// #28 POST /ai/explain
export type Explanation = {
  question_id: number;
  correct_option_id: QuizOption['id'];
  why_correct_my: string;
  why_selected_wrong_my: string | null;
  other_options_my: Partial<Record<QuizOption['id'], string>>;
};

// #9 POST /onboarding
export type OnboardingRequest = {
  last_level: 'N1' | 'N2' | 'not_taken';
  last_score: number | null;
  exam_date: string | null;
};

// #10 GET /plan
export type StudyPlan = {
  exam_date: string | null;
  days_left: number | null;
  units_total: number;
  units_done: number;
  units_per_day: number;
  finish_by: string | null;
  ai_tip_my: string | null;
  updated_at: string;
};

// #21 POST /quiz-attempts/{id}/finish
export type QuizFinish = {
  attempt_id: number;
  score: number;
  correct: number;
  total: number;
  passed: boolean;
  pass_mark: number;
  best_score: number;
  wrong_questions: number[];
};

// #22 GET /quiz-attempts/{id}
export type QuizReviewQuestion = {
  id: number;
  number: number;
  prompt_ruby: RubyPiece[];
  options: QuizOption[];
  selected_option_id: QuizOption['id'] | null;
  correct_option_id: QuizOption['id'];
  is_correct: boolean;
};

export type QuizReview = {
  attempt_id: number;
  score: number;
  passed: boolean;
  finished_at: string;
  questions: QuizReviewQuestion[];
};

// #1 GET /me
export type Me = {
  id: number;
  email: string;
  username: string;
  login_method: 'email' | 'google';
  onboarding_completed: boolean;
};

// #2, #3, #4 register / login / Google
export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  user: Me;
};

// #16 GET /bookmarks
export type SavedWord = {
  word_id: number;
  ruby: RubyPiece[];
  meaning_my: string;
  session_number: number;
  unit_number: number;
  saved_at: string;
};

export type SavedWords = { total: number; words: SavedWord[] };

// #31 GET /me/notifications, #32 PUT /me/notifications
export type NotificationSettings = {
  daily_reminder: boolean;
  reminder_time: string; // "HH:MM"
  proverb_notification: boolean;
  timezone: string; // e.g. "Asia/Tokyo"
};

// #37 POST /me/reset-progress
export type ResetResult = { round: number; plan: StudyPlan };

// #27 POST /ai/examples
export type AiItemType = 'word' | 'grammar';

export type MoreExamples = {
  item_type: AiItemType;
  item_id: number;
  examples: Example[];
  remaining_today: number;
};

// ---------- Mock test (#23 to #26) ----------

export type MockQuestion = {
  id: number;
  number: number; // 1 to 51 across the whole test
  type?: string; // language knowledge questions only, e.g. "kanji_reading"
  prompt_ruby: RubyPiece[];
  underline?: string;
  options: QuizOption[];
};

export type MockPassage = {
  id: number;
  length: 'short' | 'medium' | 'long';
  text_ruby: RubyPiece[];
  questions: MockQuestion[];
};

// #23 POST /mock-tests/{id}/attempts  (start, resume or retake; no correct answers)
export type MockAttempt = {
  attempt_id: number;
  mock_test_id: number;
  started_at: string;
  ends_at: string;
  server_time: string;
  sections: [
    { part: 'language_knowledge'; questions: MockQuestion[] },
    { part: 'reading'; passages: MockPassage[] },
  ];
  saved_answers: Record<string, QuizOption['id']>;
};

// #24 PUT /mock-attempts/{id}/answers
export type MockSaveResult = {
  question_id: number;
  saved: boolean;
  answered_count: number;
  total_questions: number;
};

export type PassPredictionWarning = 'language_knowledge_low' | 'reading_low' | 'both_low' | null;

// #25 POST /mock-attempts/{id}/submit and #26 GET /mock-attempts/{id}/result
export type MockResult = {
  attempt_id: number;
  submitted_at: string;
  submitted_by: 'user' | 'timeout';
  time_used_seconds: number;
  time_limit_seconds: number;
  score: { correct: number; total: number; percent: number };
  parts: { part: 'vocabulary' | 'grammar' | 'reading'; correct: number; total: number }[];
  pass_prediction: number | null;
  pass_prediction_warning: PassPredictionWarning;
  counts_for_prediction: boolean;
  questions: (QuizReviewQuestion & { part: 'vocabulary' | 'grammar' | 'reading' })[];
};
