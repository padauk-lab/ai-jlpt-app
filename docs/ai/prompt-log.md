# AI Prompt Log

## Attempt 1 – qwen2.5:7b, prompt v1 (2026-10-13)
- Result: answered in Japanese, not Burmese. Several wrong explanations.
- Avg time: ~23s

## Attempt 2 – qwen2.5:7b, prompt v2 (few-shot Burmese example)
- Change: added language rule + one Burmese example answer
- Result: writes in Burmese, but sentences are meaningless.
  Q2 copied the example instead of answering the real question.
- Avg time: ~138s (Burmese uses many more tokens)
- Conclusion: problem is the model, not the prompt. Small local models are not usable for Burmese.

## Attempt 3 – gemini-2.5-flash, prompt v2
- Result: natural Burmese, accurate explanations, follows JSON rules, did not copy the example.
- Avg time: ~7s
- Issues: answers too long for mobile; Q1 other-option notes give no reason;
  extra backslashes in Q4; uses loanwords like "nuance".
- Next: prompt v3 – max 3 sentences, give a reason for every option, avoid loanwords.

## Attempt 4 – gemini-2.5-flash, prompt v3 (review feedback from HP)
- Change: why_selected_wrong_my must be null when the student chose the correct answer (contract #28)
- Added Q6 (same as Q3, but selected = correct) to test this case
- Result: Q6 returned null correctly, and other_options_my listed b, c, d. Q1-Q5 still good.
- Note: Q1 says 腕力 can be read わんりき; the standard reading is わんりょく. Human review is still needed.
- Moved eval files to backend/scripts/ai_eval/ (outside the app).
- Added retry with exponential backoff (5s, 10s, 20s) for HTTP 503 from Gemini.

## Attempt 5 – gemini-3.8-flash, prompt v3 (2026-10-19)
- Speed: the first request of each run was slow (33-125s), the rest ~7-15s (3 runs)
- Answers vary between runs, so human review of cached answers is still needed

## Prompt v4 – app version (2026-10-19)
- File: backend/app/ai/prompts/explain.txt (used by explain_answer())
- Change from v3: the input now also has type, underline and passage (from the Question table),
  and every other option must have a reason
- Not tested with the real model yet. Tested with a fake AI (backend/tests/test_ai_explain.py)