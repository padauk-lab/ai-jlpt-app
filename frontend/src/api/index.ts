// The ONLY place in the app that gets data. Screens call these functions
// and never know whether the data is fake or comes from the backend.
import type { Dashboard, Proverb, SessionDetail } from './types';
import dashboardFake from './fake/dashboard.json';
import proverbFake from './fake/proverb-today.json';
import sessionFake from './fake/session-3.json';

export type { Dashboard, Proverb, SessionDetail } from './types';

// For now every function returns the contract's example data.
// When HP's endpoints are merged, each one becomes a real request to /api/v1.
function fake<T>(data: unknown): Promise<T> {
  return Promise.resolve(data as T);
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
