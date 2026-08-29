---
name: writing-plans
description: Use when you have a spec, PRD, or requirements for a multi-step task, before touching code. Creates bite-sized implementation plans in docs/plans/ with feature-map research and project-appropriate test commands.
user-invocable: true
argument-hint: "[feature or PRD to plan]"
---

# Writing Plans

Write comprehensive implementation plans assuming the engineer has zero context for this codebase. Document everything they need: which files to touch, exact code, test commands, and how to verify. Bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

**Announce at start:** "I'm using the writing-plans skill to create the implementation plan."

**REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.

## Step 1: Save Location

**Directory:** `docs/plans/` only.

**Filename:** `YYYY-MM-DD-<feature-slug>.md` (today's date, kebab-case slug).

**Example:** `docs/plans/2026-06-23-bulk-export.md`

For large features, consider **using-git-worktrees** before implementation.

## Bite-Sized Task Granularity

Each step is one action (2–5 minutes):
- "Write the failing test" — step
- "Run it to verify it fails" — step
- "Implement minimal code to pass" — step
- "Run tests and verify pass" — step
- "Commit" — step

## Plan Document Header

Every plan MUST start with:

```markdown
# [Feature Name] Implementation Plan

> **For agent:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task.
> Update each task's **Status** as work advances (not only at the end). Progress bar counts only `done` tasks.
> On resume: read **Progress** + each task's **Status** / **Resume** — do not re-do completed phases.

**Goal:** [One sentence]

**Architecture:** [2-3 sentences, grounded in feature-map]

**Areas affected:** [packages, apps, or directories from this repo]

**Tech Stack:** [Key technologies for this work]

**Feature map:** `.features/<name>.yaml` (if applicable)

**PRD:** `docs/prds/prd-<slug>.md` (if applicable — used by **ship-plan** when Progress is 100%)

## Progress

**Status:** `░░░░░░░░░░░░░░░░░░░░` 0/N done (0%) · 0 in flight

<!-- Progress bar: 20 chars. filled = round(done / total * 20). Only status `done` fills the bar.
     "in flight" = any task with status other than todo or done. -->

| # | Task | Status | Next |
|---|------|--------|------|
| 1 | [Component Name] | `todo` | implement |
| 2 | [Component Name] | `todo` | implement |
| N | [Component Name] | `todo` | implement |

---
```

### Task status model (durable — not subagent tracking)

Track **phases of the task**, not subagent IDs. Subagents are ephemeral (session-bound); the plan file is the resume source of truth.

| Status | Meaning | Progress checkbox | Counts as done? |
|--------|---------|-------------------|-----------------|
| `todo` | Not started | `[ ]` | No |
| `implementing` | Implementation in progress | `[~]` | No |
| `implemented` | Code + tests done (committed if required); **not yet verified** | `[~]` | No |
| `spec_review` | Spec review running or fixes in progress | `[~]` | No |
| `quality_review` | Spec ✅; quality review running or fixes in progress | `[~]` | No |
| `done` | Implementation + all required reviews complete | `[x]` | **Yes** |
| `blocked` | Cannot proceed; **Resume** must say why | `[!]` | No |

**Rules:**
- Only `done` advances the progress bar and `done/total`.
- `implemented` is the critical mid-state: work exists but verification has not finished — never mark `done` here.
- Do **not** store subagent IDs, chat IDs, or tool run IDs in the plan (useless on pickup).
- Do store: status, next action, commit SHA(s), open review issues, and a one-line **Resume** note.

### Progress bar rules

- Always use a **fixed width of 20** block characters.
- Formula: `filled = round(done / total * 20)` where `done` = count of tasks with status `done`.
- Line format: `` **Status:** `…bar…` D/N done (P%) · F in flight ``
- Examples:
  - nothing started → `` `░░░░░░░░░░░░░░░░░░░░` 0/10 done (0%) · 0 in flight ``
  - 3 done, task 4 implemented awaiting review → `` `██████░░░░░░░░░░░░░░` 3/10 done (30%) · 1 in flight ``
  - all done → `` `████████████████████` 10/10 done (100%) · 0 in flight ``
- The **Progress** table is the dashboard; each task body must use the same status value.
- New plans start at **0/N done (0%)** with every task `todo`.

## Task Structure

Every task has a checkbox in the heading **and** an explicit **Status** / **Resume** block (updated as work moves).

```markdown
### [ ] Task N: [Component Name]

**Status:** `todo`
**Resume:** —
**Commits:** —

**Files:**
- Create: `src/components/ExportButton.tsx`
- Modify: `src/api/exports.ts:123-145`
- Test: `src/components/ExportButton.test.tsx`

**Step 1: Write the failing test**

[Complete test code]

**Step 2: Run test to verify it fails**

Run: `npx vitest run src/components/ExportButton.test.tsx`
Expected: FAIL with [specific error]

**Step 3: Write minimal implementation**

[Complete code]

**Step 4: Run test to verify it passes**

Run: `npx vitest run src/components/ExportButton.test.tsx`
Expected: PASS

**Step 5: Commit**

```bash
git add <files>
git commit -m "feat(<scope>): <description>"
```
```

### Updating status during execution

Update the plan file **at every phase transition** (not only when fully done). Keep heading checkbox, Progress table row, and task **Status** in sync.

| When | Set **Status** | Heading | **Resume** example |
|------|----------------|---------|-------------------|
| Starting implementation | `implementing` | `[~]` | `Implementer working on steps 1–5` |
| Implementation finished, reviews not started | `implemented` | `[~]` | `Code + tests done; commit abc1234; next: spec review` |
| Spec review started / iterating | `spec_review` | `[~]` | `Spec: 2 issues open (missing index); fix then re-review` |
| Spec ✅, quality review started / iterating | `quality_review` | `[~]` | `Spec ✅; quality: naming nit in ExportButton.tsx` |
| All reviews ✅ | `done` | `[x]` | `Complete` |
| Stuck | `blocked` | `[!]` | `Blocked: needs product decision on CSV vs JSON` |

After each update:
1. Sync the Progress table row (`Status` + `Next`)
2. Recompute the **Status** bar line (`done` count + `in flight` count)

### Resume / pickup (any session)

When opening a plan mid-flight:

1. Read **Progress** table — find non-`done` tasks (especially `implemented`, `spec_review`, `quality_review`, `blocked`)
2. Open that task's **Status**, **Resume**, and **Commits**
3. Continue from **Next** / **Resume** only — do not re-implement completed phases
4. If status is `implemented` but uncommitted work exists in the tree, verify git state before re-running steps

Example mid-flight task:

```markdown
### [~] Task 2: Add export endpoint

**Status:** `implemented`
**Resume:** Implementation complete; 5/5 tests green; commit a1b2c3d. Next: spec review (not started).
**Commits:** a1b2c3d
```

## Test Commands

Put the **actual** command for this repo in each task — taken from CI, package scripts, Makefile, README, or AGENTS.md. Do not assume a stack.

Examples of commands you might find (use only what this repo actually runs):

| Stack | Typical command |
|-------|-----------------|
| Node / React | `npm test` / `npx vitest run [path]` / `npx jest [path]` |
| Python | `pytest [path]` |
| Go | `go test ./...` |

## Remember

- Exact file paths always
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Task **phases** in the plan file (not subagent IDs); bar counts only `done`
- Mid-states (`implemented`, reviews) must be written before leaving a task so pickup is safe
- Reference related skills: `verification-before-completion`, `git-commit`, `web-app-design` (if UI), `rails-feature-localizer` (if Rails UI strings)

## Execution Handoff

After saving the plan, offer execution choice:

**"Plan complete and saved to `docs/plans/<filename>`. Two execution options:**

**1. Subagent-Driven (this session)** — Fresh subagent per task, two-stage review between tasks

**2. Parallel worktree (separate session)** — Set up worktree with `using-git-worktrees`, implement in isolation

**Which approach?"**

If Subagent-Driven: use **subagent-driven-development**.
If Parallel Session: use **using-git-worktrees** first.

## Related Skills

- **product-requirements** — Upstream PRD creation
- **premortem** — Risk analysis before risky plans
- **rice** — Prioritization when choosing what to plan first
- **subagent-driven-development** — Executes this plan
- **ship-plan** — When Progress is 100% done: mark PRD Shipped and move plan + PRD to `docs/shipped/`
- **daily-log** — Changelog only (does not archive plans/PRDs)
