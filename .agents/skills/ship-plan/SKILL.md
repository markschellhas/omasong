---
name: ship-plan
description: >
  Archive a finished implementation plan: if plan Progress is fully done (100%),
  mark the linked PRD Status as Shipped, move plan + PRD into docs/shipped/,
  and optionally stamp plan-to-Done duration on a matching Basecamp card.
  Use when a plan is complete, after subagent-driven-development finishes all
  tasks, or when the user runs /ship-plan with an optional plan path.
user-invocable: true
argument-hint: "[path to plan under docs/plans/ — defaults to plan in conversation context]"
---

# Ship Plan

Mark a completed implementation plan's PRD as Shipped, move plan + PRD into `docs/shipped/`, and optionally stamp elapsed time on a matching Basecamp card.

**Announce at start:** "I'm using the ship-plan skill."

This is the housekeeper for **finished plans**. It does **not** write the changelog — use **daily-log** for that.

## Step 1: Resolve the plan file

1. If the user passed an argument (path or filename), use that under `docs/plans/` (or absolute path).
2. Else if the conversation already has an active plan path (from writing-plans / subagent-driven-development), use that.
3. Else list `docs/plans/*.md` and pick the most recently modified plan that looks complete, **or** ask the user which plan to ship.

Reject paths outside `docs/plans/` (except already-shipped files under `docs/shipped/` when re-checking). If the plan is already under `docs/shipped/`, report that and stop (unless only the PRD still needs shipping).

## Step 2: Confirm Progress is fully done

Read the plan's **Progress** section (near the top). Treat the plan as shippable only if **all** of the following hold:

1. The Progress status line shows **100%** done, e.g.:
   ```markdown
   **Status:** `████████████████████` 14/14 done (100%) · 0 in flight
   ```
2. `done` count equals total (`N/N done`).
3. Prefer also verifying the Progress **table**: every task row's Status is `` `done` `` (not `todo`, `implementing`, `implemented`, `spec_review`, `quality_review`, or `blocked`).

**If not fully done:** stop. Report current Progress (e.g. `9/14 done (64%) · 1 in flight`) and which tasks are not `done`. Do **not** change the PRD or move files.

## Step 3: Resolve the PRD

Find the PRD path from the plan, in order:

1. A line matching `**PRD:**` … (writing-plans convention), e.g.:
   - `**PRD:** `docs/prds/prd-background-jobs-hardening.md``
   - `**PRD:** docs/prds/prd-foo.md`
2. Else a markdown link to `docs/prds/` or `docs/PRDs/`.
3. Else slug heuristic: plan `YYYY-MM-DD-<slug>.md` → try `docs/prds/prd-<slug>.md` (and case variants under `docs/PRDs/`).

If no PRD is found, still move the **plan** to `docs/shipped/` after confirming with the user (or note "no PRD linked"), and skip PRD status edits.

If the PRD path does not exist on disk, stop and report the missing path.

## Step 4: Mark the PRD as Shipped

In the PRD file, set Status to **Shipped**:

- Prefer replacing an existing status line:
  - `**Status:** Draft` → `**Status:** Shipped`
  - `**Status:** Draft — …` → `**Status:** Shipped`
  - Any other `**Status:** …` → `**Status:** Shipped`
- If there is no `**Status:**` line, insert after the title (or under the first heading):
  ```markdown
  **Status:** Shipped
  ```

Do not rewrite the rest of the PRD.

## Step 5: Move plan and PRD to `docs/shipped/`

```bash
mkdir -p docs/shipped
```

Move **preserving basenames**:

```bash
mv docs/plans/<plan-filename> docs/shipped/
mv docs/prds/<prd-filename> docs/shipped/   # or docs/PRDs/ if that is the real path
```

**Conflicts:** If `docs/shipped/<same-filename>` already exists, **do not overwrite**. Report the conflict and leave the source file in place. Resolve with the user (rename, skip, or merge manually).

**Rules:**

- Never delete files — only move.
- Do not commit unless the user asks.
- On case-insensitive filesystems, `docs/prds` and `docs/PRDs` may be the same directory — use the path git reports.

## Step 6: Optional Basecamp duration stamp

If the `basecamp` CLI is available **and** a project is configured via `BASECAMP_PROJECT`, find the matching card, move it to Done if needed, and append `[duration]` to the title. Skip this step (and say so) if Basecamp is not configured or no matching card exists. Do not fail the ship.

1. List cards and match by plan path in the description, else PRD title (`PRD: …`), else plan slug:
   ```bash
   basecamp cards list --in "$BASECAMP_PROJECT" --jq '[.data[] | {id, title, completed, column: .parent.title, created_at}]'
   ```
   Then `basecamp cards show <id> --in "$BASECAMP_PROJECT" --json`.

2. If the card is not in Done, move it:
   ```bash
   basecamp cards move <id> --to "Done" --card-table <table_id> --in "$BASECAMP_PROJECT"
   ```

3. **Start** = author date of the commit that first added the plan under `docs/plans/`:
   ```bash
   git log --all --diff-filter=A --format='%aI' -- docs/plans/<plan-filename>
   ```
   If empty, the plan was never committed until this ship — **do not** use the `docs/shipped/` add commit. Use the card's `created_at` instead.

4. **End** = timeline completion event for this card (not `updated_at`):
   ```bash
   basecamp timeline --in "$BASECAMP_PROJECT" --all --jq '[.data[] | select(.kind == "kanban_card_completed") | {created_at, app_url}]'
   ```
   Use `created_at` of the event whose `app_url` contains this card id.

5. Floor to whole minutes. Omit zero units. **Never include seconds.**
   `[15m]` · `[59m]` · `[1h]` · `[1h 15m]` · `[1d 2h]` · `[2d 3h 15m]`

6. Update the title. Replace an existing trailing `[…m]` / `[…h …m]` stamp rather than appending a second one:
   ```bash
   basecamp cards update <id> --title "<original title> [<duration>]" --in "$BASECAMP_PROJECT" --json
   ```

Do not search session transcripts or feature-commit times for the clock.

## Step 7: Report

Short confirmation only:

```text
Shipped:
- Plan: docs/shipped/<plan-filename> (was N/N done 100%)
- PRD:  docs/shipped/<prd-filename> (Status → Shipped)
- Card: <full title> (start <source>, done <timeline created_at>)
```

If only the plan moved, a conflict blocked a move, Basecamp was skipped, or no card was found, say so explicitly.

Optional follow-up (do not run unless asked): "Run `/daily-log` to add today's work to `docs/changelog.md`."

## Related Skills

- **writing-plans** — Creates plans in `docs/plans/` with a `**PRD:**` line
- **subagent-driven-development** — Execute the plan; when Progress is 100% done, offer or run **ship-plan**
- **product-requirements** — Creates PRDs in `docs/prds/`
- **daily-log** — Changelog only (does **not** move plans/PRDs)

## Anti-patterns

- Do not mark a PRD Shipped if Progress is not 100% done
- Do not move unrelated files from `docs/plans/` or `docs/prds/`
- Do not invent a PRD path that is not in the plan or discoverable by slug
- Do not write changelog entries here
- Do not include seconds on the card stamp (`[1h 15m 38s]` is wrong)
- Do not use the `docs/shipped/` add commit or card `updated_at` as the duration clock
