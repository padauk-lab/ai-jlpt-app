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
  Me,
  NotificationSettings,
  QuizOption,
  QuizReview,
  ResetResult,
  SavedWords,
  SessionDetail,
  StudyPlan,
  UnitCompleteResult,
  UnitDetail,
} from './types';
import { request } from './client';

export type * from './types';
export { ApiError } from './client';
export { getMe, login, logout, register } from './auth';

// Every function here calls HP's backend. Field names follow docs/api-contract.md.

// #11 GET /dashboard
export function getDashboard(): Promise<Dashboard> {
  return request<Dashboard>('/dashboard');
}

// #12 GET /proverbs/today
export function getTodayProverb(): Promise<Proverb> {
  return request<Proverb>('/proverbs/today');
}

// #13 GET /sessions/{id}
export function getSession(id: number): Promise<SessionDetail> {
  return request<SessionDetail>(`/sessions/${id}`);
}

// #14 GET /units/{id}
export function getUnit(id: number): Promise<UnitDetail> {
  return request<UnitDetail>(`/units/${id}`);
}

// #15 POST /units/{id}/complete
export function completeUnit(id: number): Promise<UnitCompleteResult> {
  return request<UnitCompleteResult>(`/units/${id}/complete`, { method: 'POST' });
}

// #16 GET /bookmarks
export function getSavedWords(search?: string): Promise<SavedWords> {
  const query = search ? `?search=${encodeURIComponent(search)}` : '';
  return request<SavedWords>(`/bookmarks${query}`);
}

// #17 POST /bookmarks
export function saveWord(wordId: number): Promise<{ word_id: number; bookmarked: boolean }> {
  return request('/bookmarks', { method: 'POST', body: { word_id: wordId } });
}

// #18 DELETE /bookmarks/{word_id}
export function unsaveWord(wordId: number): Promise<void> {
  return request<void>(`/bookmarks/${wordId}`, { method: 'DELETE' });
}

// #19 POST /quizzes/{id}/attempts  (no correct answers are sent here)
export function startQuiz(quizId: number): Promise<QuizAttempt> {
  return request<QuizAttempt>(`/quizzes/${quizId}/attempts`, { method: 'POST' });
}

// #20 POST /quiz-attempts/{id}/answers  (instant feedback; each question once)
export function answerQuestion(attemptId: number, questionId: number, selected: QuizOption['id']): Promise<AnswerResult> {
  return request<AnswerResult>(`/quiz-attempts/${attemptId}/answers`, {
    method: 'POST',
    body: { question_id: questionId, selected_option_id: selected },
  });
}

// #21 POST /quiz-attempts/{id}/finish  (unanswered questions count as wrong)
export function finishQuiz(attemptId: number): Promise<QuizFinish> {
  return request<QuizFinish>(`/quiz-attempts/${attemptId}/finish`, { method: 'POST' });
}

// #22 GET /quiz-attempts/{id}  (review: only after finishing)
export function getQuizReview(attemptId: number): Promise<QuizReview> {
  return request<QuizReview>(`/quiz-attempts/${attemptId}`);
}

// #28 POST /ai/explain  ("Why?": only for questions the user has already answered)
export function explainAnswer(questionId: number, selected: QuizOption['id']): Promise<Explanation> {
  return request<Explanation>('/ai/explain', {
    method: 'POST',
    body: { question_id: questionId, selected_option_id: selected },
  });
}

// #9 POST /onboarding  (returns the new plan, same shape as #10)
export function submitOnboarding(answers: OnboardingRequest): Promise<StudyPlan> {
  return request<StudyPlan>('/onboarding', { method: 'POST', body: answers });
}

// #10 GET /plan
export function getPlan(): Promise<StudyPlan> {
  return request<StudyPlan>('/plan');
}

// --- Settings (#29 to #37) ---

// #29 PUT /me/study-settings  (recalculates the plan)
export function updateStudySettings(answers: OnboardingRequest): Promise<StudyPlan> {
  return request<StudyPlan>('/me/study-settings', { method: 'PUT', body: answers });
}

// #30 PUT /me  (change the username)
export function updateUsername(username: string): Promise<Me> {
  return request('/me', { method: 'PUT', body: { username } });
}

// #31 GET /me/notifications
export function getNotifications(): Promise<NotificationSettings> {
  return request<NotificationSettings>('/me/notifications');
}

// #32 PUT /me/notifications
export function updateNotifications(settings: NotificationSettings): Promise<NotificationSettings> {
  return request<NotificationSettings>('/me/notifications', { method: 'PUT', body: settings });
}

// #36 DELETE /me  (password only for email accounts)
export function deleteAccount(password: string | null): Promise<void> {
  return request<void>('/me', { method: 'DELETE', body: password ? { confirm: 'DELETE', password } : { confirm: 'DELETE' } });
}

// #37 POST /me/reset-progress
export function resetProgress(): Promise<ResetResult> {
  return request<ResetResult>('/me/reset-progress', { method: 'POST', body: { confirm: 'RESET' } });
}
