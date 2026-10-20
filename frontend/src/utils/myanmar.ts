// Small helpers for showing numbers and dates in Burmese.

const DIGITS = ['၀', '၁', '၂', '၃', '၄', '၅', '၆', '၇', '၈', '၉'];

// 3 -> ၃, 12 -> ၁၂
export function toMyanmarDigits(value: number | string): string {
  return String(value).replace(/[0-9]/g, (d) => DIGITS[Number(d)]);
}

const MONTHS = [
  'ဇန်နဝါရီ', 'ဖေဖော်ဝါရီ', 'မတ်', 'ဧပြီ', 'မေ', 'ဇွန်',
  'ဇူလိုင်', 'ဩဂုတ်', 'စက်တင်ဘာ', 'အောက်တိုဘာ', 'နိုဝင်ဘာ', 'ဒီဇင်ဘာ',
];
const WEEKDAYS = ['တနင်္ဂနွေ', 'တနင်္လာ', 'အင်္ဂါ', 'ဗုဒ္ဓဟူး', 'ကြာသပတေး', 'သောကြာ', 'စနေ'];

// "2026-12-06" -> a Date at local midnight (dates in the contract are YYYY-MM-DD)
export function parseDate(isoDate: string): Date {
  const [y, m, d] = isoDate.split('-').map(Number);
  return new Date(y, m - 1, d);
}

// "2026-12-06" -> "2026 ဒီဇင်ဘာ 6 (တနင်္ဂနွေ)"
export function formatDateMy(isoDate: string, withWeekday = true): string {
  const date = parseDate(isoDate);
  const text = `${date.getFullYear()} ${MONTHS[date.getMonth()]} ${date.getDate()}`;
  return withWeekday ? `${text} (${WEEKDAYS[date.getDay()]})` : text;
}

// "2026-11-29" -> "11/29"
export function formatShortDate(isoDate: string): string {
  const date = parseDate(isoDate);
  return `${date.getMonth() + 1}/${date.getDate()}`;
}

export function toIsoDate(date: Date): string {
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${m}-${d}`;
}

// The JLPT is held on the first Sunday of July and of December.
// Returns the next few of those dates after today, as "YYYY-MM-DD".
export function upcomingJlptDates(count = 3, from = new Date()): string[] {
  const dates: string[] = [];
  let year = from.getFullYear();
  while (dates.length < count) {
    for (const month of [6, 11]) {
      const day = new Date(year, month, 1);
      while (day.getDay() !== 0) day.setDate(day.getDate() + 1);
      if (day > from && dates.length < count) dates.push(toIsoDate(day));
    }
    year += 1;
  }
  return dates;
}

// Whole days from today until the given date.
export function daysUntil(isoDate: string, from = new Date()): number {
  const start = new Date(from.getFullYear(), from.getMonth(), from.getDate());
  return Math.round((parseDate(isoDate).getTime() - start.getTime()) / 86400000);
}
