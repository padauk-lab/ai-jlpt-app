import { getDashboard, getSession, getUnit } from './index';
import type { SavedWord, UnitDetail, Word } from './types';

// The saved words list (#16) only has each word's meaning. The full card also shows
// examples (and definitions when they exist), which come from the word's unit (#14).
// To find the unit: session number → session id (#11), unit number → unit id (#13).
// Everything is remembered while the app is open, so each unit is loaded only once.
//
// If #16 ever includes examples itself, this file can be removed.

let sessionIds: Map<number, number> | null = null;
const unitIds = new Map<number, Map<number, number>>(); // session id → (unit number → unit id)
const units = new Map<number, Promise<UnitDetail>>();

async function sessionIdFor(sessionNumber: number): Promise<number | null> {
  if (!sessionIds) {
    const dashboard = await getDashboard();
    sessionIds = new Map(dashboard.sessions.filter((s) => s.id !== null).map((s) => [s.number, s.id as number]));
  }
  return sessionIds.get(sessionNumber) ?? null;
}

async function unitIdFor(sessionId: number, unitNumber: number): Promise<number | null> {
  if (!unitIds.has(sessionId)) {
    const session = await getSession(sessionId);
    unitIds.set(sessionId, new Map(session.units.map((u) => [u.number, u.id])));
  }
  return unitIds.get(sessionId)?.get(unitNumber) ?? null;
}

function loadUnit(unitId: number): Promise<UnitDetail> {
  if (!units.has(unitId)) {
    const pending = getUnit(unitId);
    pending.catch(() => units.delete(unitId)); // allow a retry after an error
    units.set(unitId, pending);
  }
  return units.get(unitId)!;
}

export async function getWordDetails(saved: SavedWord): Promise<Word | null> {
  const sessionId = await sessionIdFor(saved.session_number);
  if (sessionId === null) return null;
  const unitId = await unitIdFor(sessionId, saved.unit_number);
  if (unitId === null) return null;
  const unit = await loadUnit(unitId);
  return unit.words.find((w) => w.id === saved.word_id) ?? null;
}

// Forget everything, e.g. after logging out or resetting progress.
export function clearWordDetails() {
  sessionIds = null;
  unitIds.clear();
  units.clear();
}
