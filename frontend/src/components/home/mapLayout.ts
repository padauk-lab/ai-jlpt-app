import type { SessionDetail } from '@/api/types';

// Turns one session from GET /sessions/{id} into the stops on the study map,
// in the order the contract's unlock rules use:
// units 1-5, quiz 1, units 6-10, quiz 2, mock test.

export type StopKind = 'unit' | 'quiz' | 'mock';
export type StopState = 'done' | 'current' | 'locked';

export type MapStop = {
  key: string;
  kind: StopKind;
  id: number;
  label: string; // unit number, or the Burmese name of the test
  state: StopState;
  x: number; // centre of the stop, in the 390 x 1000 map frame
  y: number;
};

export type MapLayout = {
  stops: MapStop[];
  currentIndex: number; // -1 when nothing is open
  goldUntil: number; // the gold path runs from stop 0 to this stop
};

const BOTTOM_Y = 935;
const STEP_Y = 70;
const CENTER_X = 195;
const SWING_X = 100;

export function buildMapLayout(session: SessionDetail): MapLayout {
  const units = [...session.units].sort((a, b) => a.number - b.number);
  const [quiz1, quiz2] = session.quizzes;

  const raw: Omit<MapStop, 'x' | 'y'>[] = [];

  const addUnit = (unit: SessionDetail['units'][number]) => {
    raw.push({
      key: `unit-${unit.id}`,
      kind: 'unit',
      id: unit.id,
      label: String(unit.number),
      state: unit.status === 'completed' ? 'done' : unit.status === 'available' ? 'current' : 'locked',
    });
  };

  const addQuiz = (quiz: SessionDetail['quizzes'][number] | undefined, title: string) => {
    if (!quiz) return;
    raw.push({
      key: `quiz-${quiz.id}`,
      kind: 'quiz',
      id: quiz.id,
      label: title,
      state: quiz.status === 'passed' ? 'done' : quiz.status === 'locked' ? 'locked' : 'current',
    });
  };

  units.slice(0, 5).forEach(addUnit);
  addQuiz(quiz1, 'စာမေးပွဲငယ် 1');
  units.slice(5, 10).forEach(addUnit);
  addQuiz(quiz2, 'စာမေးပွဲငယ် 2');

  const mock = session.mock_test;
  raw.push({
    key: `mock-${mock.id}`,
    kind: 'mock',
    id: mock.id,
    label: 'စမ်းသပ် စာမေးပွဲ',
    state: mock.status === 'completed' ? 'done' : mock.status === 'locked' ? 'locked' : 'current',
  });

  const stops = raw.map((stop, i) => ({
    ...stop,
    x: Math.round(CENTER_X + SWING_X * Math.sin(i * 0.8)),
    y: BOTTOM_Y - i * STEP_Y,
  }));

  const currentIndex = stops.findIndex((stop) => stop.state === 'current');
  let lastDone = -1;
  stops.forEach((stop, i) => {
    if (stop.state === 'done') lastDone = i;
  });

  return {
    stops,
    currentIndex,
    goldUntil: currentIndex >= 0 ? currentIndex : lastDone,
  };
}

// An SVG path through the given stops, for the road on the map.
export function pathThrough(stops: MapStop[]): string {
  return stops.map((stop, i) => `${i === 0 ? 'M' : 'L'} ${stop.x} ${stop.y}`).join(' ');
}
