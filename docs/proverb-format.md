# Content Format: Proverb List

Owner: HP (Backend). For: the content team (ANK and helpers) and their AI tools.

The Home screen shows one **proverb of the day**. Everyone sees the same proverb on the same day,
and it moves to the next one every day (Japan time). Themes: effort, consistency, never giving up, not wasting time.

## File

One file for all proverbs: `data/proverbs/proverbs.json`

## Rules

| Field | Rule |
|---|---|
| `proverbs` | 1 to 1000 proverbs. Suggested: at least 30, so there's a different one every day for a month |
| `ruby` | The proverb in Japanese, split into pieces like the unit files. Every piece with kanji needs a hiragana `reading`. Pieces without kanji have no reading |
| `meaning_my` | What it means, in Burmese |
| `explanation_my` | When and why it is used, in Burmese |

The same proverb can't appear twice.

## Example

```json
{
  "proverbs": [
    {
      "ruby": [
        { "text": "継続", "reading": "けいぞく" },
        { "text": "は" },
        { "text": "力", "reading": "ちから" },
        { "text": "なり" }
      ],
      "meaning_my": "Burmese meaning",
      "explanation_my": "Burmese explanation"
    }
  ]
}
```

(The Burmese fields must contain real Burmese text, or the check refuses them.)

## Check before opening a pull request

```
docker compose run --rm -v "$PWD/data":/data:ro backend python -m app.content.load_proverbs --check /data/proverbs/proverbs.json
```

`All N proverb(s) passed the checks.` means it's ready. To load it into your database, run the same command without `--check`.

## Changing the list later

- Fixing a proverb's Burmese text is fine: it keeps its place.
- Changing its Japanese text makes it a new proverb.
- Removing a proverb from the file switches it off. It stops appearing but isn't deleted, and putting it back switches it on again.
