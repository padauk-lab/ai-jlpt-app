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