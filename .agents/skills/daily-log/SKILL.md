---
name: daily-log
description: >
  Summarize what was shipped today from git history, prepend an entry to
  docs/changelog.md, optionally upsert that file to a Basecamp
  "Software updates" doc, and commit the changelog. Use when the user
  runs /daily-log or asks for a daily log or changelog update. Does not
  move plans or PRDs — use ship-plan for that.
user-invocable: true
argument-hint: "[date, e.g. 2026-06-25 — defaults to today]"
---

# Daily Log

Summarize what was shipped today, write it to the changelog, optionally sync a copy to Basecamp, and commit.

**Announce at start:** "I'm using the daily-log skill."

This skill updates `docs/changelog.md`, optionally upserts that file to Basecamp, and commits the changelog. It does **not** move plans or PRDs and does **not** change PRD Status — use **ship-plan** when an implementation plan is fully done.

## Step 1: Determine the target date

Use the date argument if provided. Otherwise use today's date from the system (`date +%Y-%m-%d`).

## Step 2: Pull the git log for that date

```bash
git log --oneline --after="<DATE> 00:00" --before="<DATE> 23:59:59" --format="%h %s"
```

Collect all commits. If there are none, say so and skip to Step 5 with "Nothing shipped today." (still allow writing that explicitly if useful).

## Step 3: Write a short summary

Based on the git commits (and optionally filenames recently under `docs/shipped/` for context), write 1–3 bullet points in plain language summarizing what happened that day. Think: "What did I ship today?"

Keep it short and natural. No commit hashes, no file-path housekeeping. Just the work.

Examples:
- Shipped the archive API with pagination and filtering.
- Fixed the toolbar alignment bug.
- Nothing shipped today.

## Step 4: Write to docs/changelog.md

Prepend the log entry for this date to `docs/changelog.md` (create the file if it does not exist). Format:

```markdown
## <DATE>

- <bullet point>
- <bullet point>
```

Keep it to the same 1–3 bullet points from Step 3. Prepend so the newest entry is always at the top; keep a `# Changelog` heading at the very top of the file.

If `docs/changelog.md` already has an entry for this date, update it in place rather than adding a duplicate.

## Step 5: Optional Basecamp "Software updates"

If the `basecamp` CLI is available **and** a project is configured via the `BASECAMP_PROJECT` environment variable, copy the full `docs/changelog.md` to that project as a document titled **Software updates**. Otherwise skip this step and say so.

Documents accept Markdown. Pass the file body as a real argument via Python — `files documents create` / `files update --content` treat `-` as the literal character `-`, not stdin.

1. Find an existing active doc with that exact title (search the whole project, not just the root folder):

```bash
basecamp recordings documents --in "$BASECAMP_PROJECT" --all --jq '.data[] | select(.title == "Software updates") | .id'
```

2. If an id is returned, replace its content with the changelog:

```bash
python3 -c 'import os,pathlib,subprocess,sys
doc_id=sys.argv[1]
project=os.environ["BASECAMP_PROJECT"]
body=pathlib.Path("docs/changelog.md").read_text()
subprocess.run(["basecamp","files","update",doc_id,"--content",body,"--in",project,"--json"],check=True)' <DOC_ID>
```

3. If no id is returned, create the doc in the project root, silently:

```bash
python3 -c 'import os,pathlib,subprocess
project=os.environ["BASECAMP_PROJECT"]
body=pathlib.Path("docs/changelog.md").read_text()
subprocess.run(["basecamp","files","documents","create","Software updates",body,"--in",project,"--no-subscribe","--json"],check=True)'
```

Run this step whenever `docs/changelog.md` exists and Basecamp is configured, even if nothing shipped today. Report the Basecamp doc URL (from the CLI JSON) so the user can open it.

## Step 6: Commit the changelog

Always commit `docs/changelog.md` before finishing. Follow **git-commit** for the message. Stage only that file. Skip **verification-before-completion** (docs-only). Suggested message:

```
docs: add daily log for <DATE>
```

If `docs/changelog.md` is unchanged, skip the commit and say so.

## Step 7: Output the daily log

Print the same 1–3 bullet points to the conversation so the user can see them without opening the file.

If nothing happened on the target date, say so explicitly rather than printing an empty log.

## Rules

- Do **not** move files out of `docs/plans/` or `docs/prds/`.
- Do **not** edit PRD or plan Status fields.
- The final output is the bullet points, plus the Basecamp doc URL if synced. No tables, no commit lists.

## Related Skills

- **ship-plan** — When a plan is 100% done: mark PRD Shipped and move plan + PRD to `docs/shipped/`
- **git-commit** — Conventional commit message for the changelog commit
