# How we work

## Workflow
1. Pick a task (Issue) from the Project board and move it to In progress
2. Pull the latest main: git checkout main && git pull
3. Create a branch: git checkout -b feature/short-name (or fix/short-name)
4. Make small commits with clear messages, for example "Add score validation to onboarding form"
5. Push your branch: git push -u origin feature/short-name
6. Open a pull request on GitHub, link the Issue, describe your change in 2 or 3 sentences
7. One teammate reviews it, fix their comments, then merge
8. Move the Issue to Done

## Rules
- Never push directly to main
- Never commit .env, API keys or passwords
- Stay inside your own folder, ask before changing someone else's area
- If a merged change breaks the app, undo it with git revert
- Commit with the email linked to your GitHub account
- Using AI is fine, but you must be able to explain everything you commit

## Review checklist
- Does what the Issue asked, nothing more
- App still runs
- Files changed are in the author's own area
- No secrets included
- Clear names and messages
