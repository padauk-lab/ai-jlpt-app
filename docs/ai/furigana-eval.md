# Furigana Evaluation: AI vs pykakasi

Question: for "More examples" (contract endpoint 27), who should write the ruby (furigana)?
Author: SWYH · Date: 2026-10-23

## Method
- Ground truth: the human-checked example sentences in `data/units/` (378 sentences, Session 1).
- Removed the readings, then asked each method to add them again, and compared the reading of the whole sentence
  (so different piece splits like 世界中 vs 世界+中 do not count as errors).
- Scripts: `backend/scripts/ai_eval/furigana_eval.py` (AI), `backend/scripts/ai_eval/pykakasi_eval.py` (code).

## Results

| Method | Reading correct | Ruby rules followed |
|---|---|---|
| gemini-3.8-flash | 337/340 (99.1%) | 340/340 |
| pykakasi (dictionary, no context) | 306/378 (81.0%) | not applicable |

The AI run stopped at 340 sentences because of the free-tier daily quota.

## Errors
- AI (3): 通じて → とおじて, 守る → まぼる, 前社長 → まえしゃちょう. All three are common kanji, not the N1 target words.
- pykakasi (72): cannot use context, e.g. 彼 → かの, 人 → にん, 入った → いっった, 労う → らうう, 車離れ → くるまはなれ.
- Both got 前社長 wrong. Our checked data was correct in every case.

## Decision
The AI writes the ruby. pykakasi is not added as a dependency.
With 99.1% per sentence, about 1 in 40 "More examples" taps may have one wrong reading.
The code still checks the ruby rules (readings only on kanji, hiragana only, text unchanged).

## Notes
- Free tier: about 320 sentences per day, and some batches took 3-5 minutes. Production needs the paid tier.
- Idea for later: a "Report a mistake" button for AI examples.