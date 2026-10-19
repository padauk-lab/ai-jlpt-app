# Content Format: Mock Test Files

Owner: HP (Backend). For: the content team (ANK and helpers) and their AI tools.

Each session ends with one **mock test** in the JLPT N1 Language Knowledge format:
**45 vocabulary and grammar questions**, plus **3 reading passages** (short, medium, long) with their own questions.
It is timed by the server (30 minutes by default). There is no feedback until the user submits.
Retakes use the same questions.

## File name and place

`data/mock_tests/sNN_mock.json`. Examples: `data/mock_tests/s01_mock.json`, `data/mock_tests/s12_mock.json`.

## Rules

| Field | Rule |
|---|---|
| `session_number` | 1 to 20, same as the file name |
| `time_limit_minutes` | Optional, 1 to 180. Default 30 |
| `questions` | Exactly 45 language knowledge questions, numbered 1 to 45 in order. Needs both vocabulary and grammar |
| `passages` | Exactly 3, in this order: `"short"`, `"medium"`, `"long"`. Each has `text_ruby` and 1 to 10 questions |
| Reading question numbers | Continue after 45 in order: 46, 47, 48 and so on, across the 3 passages |

**Language knowledge questions** use the same fields and rules as quiz questions (see `docs/content-format.md`):
`number`, `part`, `type`, `prompt_ruby`, `underline`, `options`, `correct_option_id`. Differences:
- `unit_number` is optional (any unit 1 to 10 of the session). Add it when you can, it helps the review screen.
- `word_position` is optional, and only together with `unit_number`.

**Reading questions** have only `number`, `prompt_ruby`, `options` and `correct_option_id`.

Which split of vocabulary and grammar to use is open decision #2 (ANK to confirm against the real N1 format).
The loader only checks that both are there.

## Example (shortened)

```json
{
  "session_number": 1,
  "time_limit_minutes": 30,
  "questions": [
    {
      "number": 1,
      "part": "vocabulary",
      "type": "kanji_reading",
      "unit_number": 1,
      "word_position": 3,
      "prompt_ruby": [
        { "text": "政府", "reading": "せいふ" },
        { "text": "は物価の上昇を" },
        { "text": "抑制" },
        { "text": "する方針だ。" }
      ],
      "underline": "抑制",
      "options": [
        { "id": "a", "text": "ようせい" },
        { "id": "b", "text": "よくせい" },
        { "id": "c", "text": "おくせい" },
        { "id": "d", "text": "よくぜい" }
      ],
      "correct_option_id": "b"
    }
  ],
  "passages": [
    {
      "length": "short",
      "text_ruby": [
        { "text": "継続", "reading": "けいぞく" },
        { "text": "は力なりと言うが、……" }
      ],
      "questions": [
        {
          "number": 46,
          "prompt_ruby": [{ "text": "筆者の考えに合うものはどれか。" }],
          "options": [
            { "id": "a", "text": "……" },
            { "id": "b", "text": "……" },
            { "id": "c", "text": "……" },
            { "id": "d", "text": "……" }
          ],
          "correct_option_id": "c"
        }
      ]
    }
  ]
}
```

(A real file has all 45 language knowledge questions and all 3 passages.)

## Check before opening a pull request

Load the units first (the session must exist), then check:

```
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_mock_tests --check /data/mock_tests
```

## Changing a mock test later

- Fixing text, options or answers is fine. Keep the `number`. Saved "Why?" explanations for changed questions are cleared. If a passage's text changes, all of its questions lose them.
- Once anyone has started the mock test, questions can be fixed but not removed.
