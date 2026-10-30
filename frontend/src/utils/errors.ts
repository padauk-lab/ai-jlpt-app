import { ApiError } from '@/api/client';

// Burmese messages for the backend's error codes (contract "Errors").
// The backend's own message is English, so the app shows these instead.
const MESSAGES: Record<string, string> = {
  network_error: 'ဆာဗာကို ချိတ်ဆက်၍ မရပါ။ အင်တာနက်ကို စစ်ပြီး ပြန်ကြိုးစားပါ။',
  wrong_login: 'အီးမေးလ် သို့မဟုတ် စကားဝှက် မှားနေပါတယ်။ ပြန်စစ်ပြီး ထပ်ကြိုးစားပါ။',
  email_taken: 'ဒီအီးမေးလ်နဲ့ အကောင့် ရှိပြီးသားပါ။',
  username_taken: 'ဒီအသုံးပြုသူအမည်ကို တခြားသူ သုံးပြီးသားပါ။',
  already_registered: 'ဒီအီးမေးလ် ဒါမှမဟုတ် အသုံးပြုသူအမည်ကို သုံးပြီးသားပါ။',
  validation_error: 'ထည့်ထားတာတွေထဲမှာ မမှန်တာ ရှိပါတယ်။',
  unit_locked: 'ဒီယူနစ်က သော့ခတ်ထားဆဲပါ။',
  session_locked: 'ဒီအပိုင်းက သော့ခတ်ထားဆဲပါ။',
  quiz_locked: 'ဒီစာမေးပွဲငယ်က သော့ခတ်ထားဆဲပါ။',
  onboarding_not_done: 'အရင်ဆုံး မေးခွန်း ၃ ခု ဖြေပေးပါ။',
  already_answered: 'ဒီမေးခွန်းကို ဖြေပြီးသားပါ။',
  attempt_finished: 'ဒီစာမေးပွဲငယ် ပြီးသွားပါပြီ။',
  attempt_not_finished: 'စာမေးပွဲငယ်ကို အရင် ပြီးအောင် ဖြေပါ။',
  not_answered_yet: 'အရင် ဖြေပြီးမှ ရှင်းလင်းချက် ကြည့်လို့ရပါမယ်။',
  ai_unavailable: 'AI ဆရာ ခဏ အလုပ်များနေပါတယ်။ နောက်မှ ပြန်ကြိုးစားပါ။',
};

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 429) {
      const wait = error.retryAfter ? ` ${error.retryAfter} စက္ကန့် အကြာမှာ ပြန်ကြိုးစားနိုင်ပါမယ်။` : '';
      return `ခဏလေး စောင့်ပေးပါ။${wait}`;
    }
    if (MESSAGES[error.code]) return MESSAGES[error.code];
  }
  return 'တစ်ခုခု မှားသွားပါတယ်။ ခဏနေမှ ပြန်ကြိုးစားပါ။';
}
