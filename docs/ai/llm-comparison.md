# LLM Comparison for Burmese Explanations

Answers Open question 4 (LLM choice) in `docs/api-contract.md`.
Author: SWYH · Date: 2026-10-13

## Test setup
- 5 N1 questions (kanji reading, vocabulary, grammar): `backend/scripts/ai_eval/test_questions.json`
- Same prompt for every model ("Why?" explanation, contract #28 JSON shape): `prompt_explain_v2.txt`
- Script: `backend/scripts/ai_eval/compare_llms.py`
- Each answer checked by hand (scores 0-5)

## Results

| Criteria | qwen2.5:7b (local) | gemini-2.5-flash (cloud) |
|---|---|---|
| Writes in Burmese | 5 | 5 |
| Burmese is natural and clear | 0 | 5 |
| Explanation is correct | 0 | 5 |
| Follows JSON rules | 4 | 5 |
| Avg time per answer | ~138s | ~7s |
| Cost | Free (runs on laptop) | Free tier, paid for production |

## Findings
1. **qwen2.5:7b is not usable.** With prompt v1 it answered in Japanese.
   With a Burmese example (v2) it wrote Burmese, but the sentences had no meaning,
   and on Q2 it copied the example instead of answering the real question.
2. **gemini-2.5-flash works well.** Natural Burmese, correct grammar explanations,
   everyday examples, and it followed the JSON rules on all 5 questions.
3. **Burmese is slow and expensive in tokens.** The same model took ~6x longer when
   writing Burmese. This supports the contract's plan to cache "Why?" explanations.

## Recommendation
Use **gemini-2.5-flash** for "Why?", "More examples" and the study plan tip.

## Open points for the team
- Free-tier data may be used by Google to improve its products. Fine for development;
  production should use the paid tier.
- Add `GEMINI_API_KEY=your-key-here` to `.env.example` (root file, owner: team lead).
- Next prompt version (v3): shorter answers for mobile, a reason for every option,
  avoid loanwords like "nuance".

## Update 2026-10-19: newer model (gemini-3.8-flash)

Answers the follow-up from HP on #26: test one newer Gemini model.
Listed available models with `backend/scripts/ai_eval/list_models.py` and picked the newest stable Flash model
(no "preview" or codename, same tier as 2.5-flash). Same prompt v3 and 6 questions, 3 runs.

| Criteria | gemini-2.5-flash | gemini-3.8-flash |
|---|---|---|
| Natural Burmese | 5 | 5 |
| Correct explanations | 5 | 5 (more precise, e.g. explains why はずだ contradicts the sentence) |
| Reason for every other option | Sometimes missing | Usually given (missing once in 3 runs) |
| Q6 null case | Pass | Pass (3/3 runs) |

| Time (s) | Run 1 | Run 2 | Run 3 |
|---|---|---|---|
| Q1 (first request) | 125.5 | 33.5 | 91.1 |
| Q2-Q6 | 7-139 | 6-15 | 7-9 |

Findings:
1. **The first request of each run is slow (30-125s)**, the rest are ~7-15s. Likely a cold start.
   The backend route needs a long timeout, or returns 503 "Try again later".
2. Run 1 also had 120-140s answers and one HTTP 503 (server load). One run is not enough to judge speed.
3. **Answers change between runs** (e.g. Q1 gave a correct example in run 2 and a doubtful one in run 3).
   This supports caching "Why?" once and having ANK review it.

**Recommendation:** `LLM_MODEL=gemini-3.8-flash`. Fallback: `gemini-2.5-flash` (change `.env` only, no code change).

Notes:
- Use exact version names, not aliases like `gemini-flash-latest`, so results stay the same.
- Cost of 3.8-flash vs 2.5-flash is not checked yet.
- "More examples" is not cached, so slow first requests affect users there.



Full prompt history: `docs/ai/prompt-log.md`