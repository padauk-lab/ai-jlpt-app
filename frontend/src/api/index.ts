// The ONLY place in the app that gets data. Screens call these functions
// and never know whether the data is fake or comes from the backend.
import type {
  AnswerResult,
  Dashboard,
  Explanation,
  OnboardingRequest,
  Proverb,
  QuizAttempt,
  QuizFinish,
  QuizOption,
  QuizReview,
  SessionDetail,
  StudyPlan,
  UnitCompleteResult,
  UnitDetail,
} from './types';
import dashboardFake from './fake/dashboard.json';
import planFake from './fake/plan.json';
import proverbFake from './fake/proverb-today.json';
import quizAttemptFake from './fake/quiz-5-attempt.json';
import quizServerFake from './fake/quiz-5-server.json';
import sessionFake from './fake/session-3.json';
import unitFake from './fake/unit-25.json';

export type * from './types';

// For now every function returns the contract's example data.
// When HP's endpoints are merged, each one becomes a real request to /api/v1.
function fake<T>(data: unknown, delayMs = 0): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(data as T), delayMs));
}

// #11 GET /dashboard
export function getDashboard(): Promise<Dashboard> {
  return fake<Dashboard>(dashboardFake);
}

// #12 GET /proverbs/today
export function getTodayProverb(): Promise<Proverb> {
  return fake<Proverb>(proverbFake);
}

// #13 GET /sessions/{id}
export function getSession(_id: number): Promise<SessionDetail> {
  return fake<SessionDetail>(sessionFake);
}

// #14 GET /units/{id}
export function getUnit(_id: number): Promise<UnitDetail> {
  return fake<UnitDetail>(unitFake);
}

// #15 POST /units/{id}/complete
export function completeUnit(id: number): Promise<UnitCompleteResult> {
  return fake<UnitCompleteResult>({ unit_id: id, status: 'completed', next: { type: 'quiz', id: 5 } });
}

// #19 POST /quizzes/{id}/attempts
export function startQuiz(_quizId: number): Promise<QuizAttempt> {
  return fake<QuizAttempt>(quizAttemptFake);
}

// #20 POST /quiz-attempts/{id}/answers
// The fake "server" checks the answer and remembers it, just like the real one will.
const PASS_MARK = 70;
let picks: Record<number, QuizOption['id']> = {};
let bestScore = 0;

function fakeAnswers() {
  return quizServerFake.answers as Record<string, QuizOption['id']>;
}

function countCorrect() {
  const answers = fakeAnswers();
  return Object.entries(picks).filter(([id, pick]) => answers[id] === pick).length;
}

export function answerQuestion(
  _attemptId: number,
  questionId: number,
  selected: QuizOption['id'],
): Promise<AnswerResult> {
  const correct = fakeAnswers()[String(questionId)];
  picks[questionId] = selected;
  return fake<AnswerResult>({
    question_id: questionId,
    is_correct: selected === correct,
    selected_option_id: selected,
    correct_option_id: correct,
    answered: Object.keys(picks).length,
    correct_so_far: countCorrect(),
  });
}

export function resetFakeQuiz() {
  picks = {};
}

// #21 POST /quiz-attempts/{id}/finish  (unanswered questions count as wrong)
export function finishQuiz(attemptId: number): Promise<QuizFinish> {
  const answers = fakeAnswers();
  const questions = (quizAttemptFake as QuizAttempt).questions;
  const correct = countCorrect();
  const score = Math.round((correct / questions.length) * 100);
  bestScore = Math.max(bestScore, score);
  return fake<QuizFinish>({
    attempt_id: attemptId,
    score,
    correct,
    total: questions.length,
    passed: score >= PASS_MARK,
    pass_mark: PASS_MARK,
    best_score: bestScore,
    wrong_questions: questions.map((q) => q.id).filter((id) => picks[id] !== answers[String(id)]),
  });
}

// #22 GET /quiz-attempts/{id}  (after finishing, the correct answers may be shown)
export function getQuizReview(attemptId: number): Promise<QuizReview> {
  const answers = fakeAnswers();
  const questions = (quizAttemptFake as QuizAttempt).questions.map((q) => {
    const selected = picks[q.id] ?? null;
    const correct = answers[String(q.id)];
    return {
      id: q.id,
      number: q.number,
      prompt_ruby: q.prompt_ruby,
      options: q.options,
      selected_option_id: selected,
      correct_option_id: correct,
      is_correct: selected === correct,
    };
  });
  const score = Math.round((questions.filter((q) => q.is_correct).length / questions.length) * 100);
  return fake<QuizReview>({
    attempt_id: attemptId,
    score,
    passed: score >= PASS_MARK,
    finished_at: new Date().toISOString(),
    questions,
  });
}

// #28 POST /ai/explain
type FakeExplanation = { why_correct_my: string; options: Partial<Record<QuizOption['id'], string>> };
export function explainAnswer(questionId: number, selected: QuizOption['id']): Promise<Explanation> {
  const answers = quizServerFake.answers as Record<string, QuizOption['id']>;
  const all = quizServerFake.explanations as Record<string, FakeExplanation>;
  const correct = answers[String(questionId)];
  const item = all[String(questionId)];
  const others = { ...item.options };
  delete others[selected];
  return fake<Explanation>(
    {
      question_id: questionId,
      correct_option_id: correct,
      why_correct_my: item.why_correct_my,
      why_selected_wrong_my: selected === correct ? null : (item.options[selected] ?? null),
      other_options_my: others,
    },
    600,
  );
}

// #9 POST /onboarding  (returns the new plan, same shape as #10)
export function submitOnboarding(_answers: OnboardingRequest): Promise<StudyPlan> {
  return fake<StudyPlan>(planFake, 1500);
}

// #10 GET /plan
export function getPlan(): Promise<StudyPlan> {
  return fake<StudyPlan>(planFake);
}
