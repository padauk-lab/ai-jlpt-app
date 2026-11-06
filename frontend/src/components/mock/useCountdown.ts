import { useEffect, useRef, useState } from 'react';

// Seconds left until `endsAt`, timed by the server's clock (contract #23):
// the difference between server_time and this phone's clock is measured once,
// so a wrong phone clock doesn't change the time limit.
export function useCountdown(endsAt: string | null, serverTime: string | null): number | null {
  const offset = useRef(0); // server clock minus phone clock, in ms
  const [left, setLeft] = useState<number | null>(null);

  useEffect(() => {
    if (!endsAt || !serverTime) return;
    offset.current = new Date(serverTime).getTime() - Date.now();
    const end = new Date(endsAt).getTime();
    const tick = () => setLeft(Math.max(0, Math.round((end - (Date.now() + offset.current)) / 1000)));
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [endsAt, serverTime]);

  return left;
}

export function formatClock(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
}
