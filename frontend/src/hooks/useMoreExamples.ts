import { useCallback, useRef, useState } from 'react';
import { moreExamples } from '@/api';
import { ApiError } from '@/api/client';
import type { AiItemType, Example } from '@/api/types';

const MSG = {
  limit: 'ယနေ့အတွက် ဥပမာ တောင်းနိုင်သည့် အကြိမ်ရေ ပြည့်သွားပါပြီ။ မနက်ဖြန် ပြန်ကြိုးစားပါ။',
  tryLater: 'ခဏနေမှ ပြန်ကြိုးစားပေးပါ။',
  locked: 'ဤယူနစ်ကို မဖွင့်ရသေးပါ။',
  generic: 'တစ်ခုခု မှားယွင်းသွားပါသည်။ ထပ်ကြိုးစားပါ။',
};

const keyOf = (type: AiItemType, id: number) => `${type}:${id}`;

export function useMoreExamples() {
  const [extra, setExtra] = useState<Record<string, Example[]>>({});
  const [errors, setErrors] = useState<Record<string, string | undefined>>({});
  const [loadingKey, setLoadingKey] = useState<string | null>(null);
  const [remaining, setRemaining] = useState<number | null>(null);
  const busy = useRef(false);

  const load = useCallback(async (type: AiItemType, id: number) => {
    if (busy.current || remaining === 0) return;
    busy.current = true;
    const key = keyOf(type, id);
    setLoadingKey(key);
    setErrors((e) => ({ ...e, [key]: undefined }));

    try {
      const res = await moreExamples(type, id);
      setExtra((prev) => ({ ...prev, [key]: [...(prev[key] ?? []), ...res.examples] }));
      setRemaining(res.remaining_today);
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      if (status === 429) setRemaining(0);
      const msg =
        status === 429 ? MSG.limit :
        status === 503 ? MSG.tryLater :
        status === 403 ? MSG.locked : MSG.generic;
      setErrors((e) => ({ ...e, [key]: msg }));
    } finally {
      busy.current = false;
      setLoadingKey(null);
    }
  }, [remaining]);

  return {
    load,
    remaining,
    examplesFor: (type: AiItemType, id: number) => extra[keyOf(type, id)] ?? [],
    errorFor: (type: AiItemType, id: number) => errors[keyOf(type, id)],
    isLoading: (type: AiItemType, id: number) => loadingKey === keyOf(type, id),
  };
}