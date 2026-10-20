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
  sessions: { id: number; number: number; progress: number; status: SessionStatus }[];
};

// #12 GET /proverbs/today
export type Proverb = {
  id: number;
  ruby: RubyPiece[];
  meaning_my: string;
  explanation_my: string;
};

// #13 GET /sessions/{id}
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
  mock_test: {
    id: number;
    status: MockTestStatus;
    best_score: number | null;
    last_score: number | null;
    attempts: number;
  };
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
  grammar: Grammar;
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
