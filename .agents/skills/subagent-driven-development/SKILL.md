---
name: subagent-driven-development
description: Use when executing implementation plans with independent tasks in the current session. Dispatches a fresh subagent per task with two-stage review — spec compliance first, then code quality.
user-invocable: true
argument-hint: "[plan file path]"
---

# Subagent-Driven Development

Execute a plan by dispatching a fresh subagent per task, with two-stage review after each: spec compliance first, then code quality.

**Core principle:** Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

- You have an implementation plan (`docs/plans/*.md` from **writing-plans**)
- Tasks are mostly independent
- Staying in this session (no context switch to a new chat)

**Don't use when:**
- No plan exists yet → use **writing-plans** first
- Tasks are tightly coupled → execute sequentially yourself
- Need parallel session isolation → use **using-git-worktrees** instead

## The Process

### Setup

1. Read plan file: `docs/plans/<file>.md`
2. **Resume first:** Use the Progress table + each task's **Status** / **Resume** / **Commits**.
   - Skip tasks already `done`
   - For `implemented` / `spec_review` / `quality_review` / `blocked`, continue from that phase — do not re-implement
   - Never rely on prior session memory or subagent IDs (they are not tracked)
3. **REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.
4. Extract remaining work with full task text and context
5. Create TodoWrite from non-`done` tasks (reflect current phase in the todo text)

### Per Task

Update the **plan file at every phase change** (see **writing-plans** status model). Subagents execute work; the plan records durable phase — not subagent IDs.

```
1. Set Status → implementing; sync Progress table; note Resume
2. Dispatch implementer subagent (see references/implementer-prompt.md)
3. Answer any questions before letting them proceed
4. Implementer implements, tests, commits, self-reviews
5. Set Status → implemented; record commit SHA(s) in **Commits**;
   Resume: "next: spec review". Sync Progress (still not done — bar unchanged)
6. Dispatch spec reviewer (see references/spec-reviewer-prompt.md)
   Set Status → spec_review while running / fixing
   → If issues: implementer fixes → re-review until ✅
   → On each loop, update Resume with open issues
7. Dispatch code quality reviewer (see references/code-quality-reviewer-prompt.md)
   Set Status → quality_review while running / fixing
   → If issues: implementer fixes → re-review until ✅
8. Set Status → done; heading [x]; Resume: Complete; sync Progress bar
9. Mark task complete in TodoWrite
10. Next incomplete task (by Status, not by assumption)
```

**If the session ends mid-task:** plan Status must already reflect the last completed phase
(e.g. `implemented` + commit SHA). Pickup reads that and resumes at the next phase.

### After All Tasks

1. Confirm plan **Progress** is 100% (all tasks `done`, bar full, 0 in flight)
2. Run full verification per **verification-before-completion**
3. Dispatch final reviewer for entire implementation (optional)
4. Offer **ship-plan** (marks linked PRD Shipped; moves plan + PRD to `docs/shipped/`)
5. Offer PR creation or merge

## Prompt Templates

- `references/implementer-prompt.md` — Dispatch implementer subagent
- `references/spec-reviewer-prompt.md` — Spec compliance review
- `references/code-quality-reviewer-prompt.md` — Code quality review

Use this environment's subagent / Task tool (`general-purpose` or `code-reviewer` as appropriate).

## Example Workflow

```
You: I'm using subagent-driven-development to execute this plan.

[Read docs/plans/2026-06-23-bulk-export.md]
[Progress: Task 1 done; Task 2 Status=implemented, Resume="next: spec review", commit a1b2c3d]
[Skip Task 1. Resume Task 2 at spec review — do not re-implement]
[TodoWrite from incomplete tasks only]

Task 2: Add export endpoint (resume)

[Set Status → spec_review]
[Dispatch spec reviewer with Task 2 text + commit a1b2c3d context]
→ ✅ compliant
[Set Status → quality_review]
[Dispatch code quality reviewer → ✅ approved]
[Set Status → done; Progress bar +1; Mark TodoWrite complete]

Task 3: Add UI button (Status=todo → full pipeline)...
[Repeat from implementing]
```

## Red Flags

**Never:**
- Skip reviews (spec OR code quality)
- Proceed with unfixed review issues
- Dispatch multiple implementers in parallel (file conflicts)
- Make subagent read plan file (provide full task text)
- Start code quality review before spec compliance is ✅
- Move to next task while either review has open issues
- Mark a task `done` when only implementation finished (use `implemented`)
- Track or depend on subagent IDs for resume (use Status / Resume / Commits)
- Leave a phase transition unwritten in the plan before context-switching or ending the session

**If reviewer finds issues:**
- Same implementer fixes them
- Reviewer reviews again
- Repeat until approved
- Keep Status on `spec_review` or `quality_review` and list open issues in Resume until ✅

## Notes

- Provide this repo's actual test commands in each task prompt
- UI tasks: note follow-up for `web-app-design` and, if Rails i18n applies, `rails-feature-localizer`
- Cross-package tasks: complete the contract-owning side before dispatching the consumer
- Commits follow **git-commit** conventions with package/app scope when isolated

## Related Skills

- **writing-plans** — Creates the plan this skill executes
- **verification-before-completion** — Before claiming task/plan complete
- **git-commit** — Conventional commits per task
- **systematic-debugging** — When a task hits unexpected failures
- **dispatching-parallel-agents** — For independent failures, not sequential plan tasks
- **receiving-code-review** — When acting on review feedback between tasks