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
