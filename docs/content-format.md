# Content Format: Quiz Question Files

Owner: HP (Backend). For: the content team (ANK and helpers) and their AI tools.

Each session has 2 quizzes: **Quiz 1** tests units 1 to 5, **Quiz 2** tests units 6 to 10.
Each quiz is one JSON file with a **question bank**. Every attempt picks 20 questions at random from the bank,
so retakes get a different mix.

## File name and place

`data/quizzes/sNN_qN.json`. Examples: `data/quizzes/s01_q1.json`, `data/quizzes/s01_q2.json`, `data/quizzes/s12_q2.json`.

## Rules

| Field | Rule |
|---|---|
| `session_number` | 1 to 20, same as the file name |
| `quiz_number` | 1 or 2, same as the file name |
| `questions` | At least 20, at most 100. Suggested: 40, so retakes feel different |
| `number` | 1, 2, 3 and so on, each used once. **Never give an old number to a different question**: the number is how the app keeps users' past answers |
| `part` | `"vocabulary"` or `"grammar"`. Every quiz needs some of both |
| `type` | Vocabulary: `"kanji_reading"`, `"context"`, `"paraphrase"`, `"usage"`. Grammar: `"grammar_form"`, `"sentence_order"` |
| `unit_number` | The unit it tests. Quiz 1: 1 to 5. Quiz 2: 6 to 10 |
| `word_position` | Vocabulary only: which word of that unit (1 to 20). Leave it out for grammar (it tests the unit's grammar pattern) |
| `prompt_ruby` | The question sentence, split into pieces like the unit files. A `reading` is **optional** here, and only allowed on pieces with kanji |
| `underline` | The part being tested. Must be exactly one piece of `prompt_ruby`. Needed for `kanji_reading`, `paraphrase` and `usage` |
| `options` | Exactly 4: `a`, `b`, `c`, `d` in that order, all different |
| `correct_option_id` | `"a"`, `"b"`, `"c"` or `"d"`. Mix them up, don't always use `a` |

Extra rules for `kanji_reading`:
- The tested word must **not** have a `reading` (it would show the answer).
- All 4 options must be hiragana.
- If the tested word is the unit's word, the correct option must match the unit's reading.

## Example

```json
{
  "session_number": 1,
  "quiz_number": 1,
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
    },
    {
      "number": 2,
      "part": "grammar",
      "type": "grammar_form",
      "unit_number": 1,
      "prompt_ruby": [
        { "text": "彼", "reading": "かれ" },
        { "text": "は足のけが（　）、最後まで走り抜いた。" }
      ],
      "options": [
        { "id": "a", "text": "をものともせず" },
        { "id": "b", "text": "にかかわらず" },
        { "id": "c", "text": "をきっかけに" },
        { "id": "d", "text": "にこたえて" }
      ],
      "correct_option_id": "a"
    }
  ]
}
```

(A real file needs at least 20 questions.)

## Check before opening a pull request

Load the units first, because a quiz can only test units that are in the database. Then check the quiz files:

```
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_units /data/units
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_quizzes --check /data/quizzes
```

`All N quiz file(s) passed the checks.` means it's ready. Otherwise every problem is listed with the file and question number.

GitHub also runs this check automatically on every pull request (together with the units, mock tests and proverbs).
A red X on the pull request means a content file has a problem: open "Details" to see which one.
To run the same full check yourself:

```
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.check_all /data
```

## Changing a question later

- Fixing a question's text, options or answer is fine. Keep its `number`. Its saved "Why?" explanations are cleared, so the AI writes new ones.
- Removing a question is only possible while nobody has answered it. After that, fix it instead of removing it.
