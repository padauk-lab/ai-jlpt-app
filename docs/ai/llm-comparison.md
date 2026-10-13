# LLM Comparison for Burmese Explanations

Answers Open question 4 (LLM choice) in `docs/api-contract.md`.
Author: SWYH · Date: 2026-10-13

## Test setup
- 5 N1 questions (kanji reading, vocabulary, grammar): `backend/app/ai/eval/test_questions.json`
- Same prompt for every model ("Why?" explanation, contract #28 JSON shape): `prompt_explain_v2.txt`
- Script: `backend/app/ai/eval/compare_llms.py`
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

Full prompt history: `docs/ai/prompt-log.md`