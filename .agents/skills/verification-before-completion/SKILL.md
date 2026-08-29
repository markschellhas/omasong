---
name: verification-before-completion
description: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs. Requires running verification commands and confirming output before any success claims — evidence before assertions always.
user-invocable: true
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Finding verification commands

Use the commands this repo actually runs — from CI, package scripts, Makefile, README, or AGENTS.md. Do not assume a stack or directory layout.

| Claim | How to prove it |
|-------|-----------------|
| Tests pass | Run this project's test command for the affected area |
| Single test | The project's single-file / single-example invocation |
| Build succeeds | Project-appropriate build command with exit 0 |
| Bug fixed | Reproduce original symptom — must no longer occur |
| i18n complete | Grep for hardcoded strings in changed UI |
| Feature correct | Re-read plan/PRD checklist line by line |

Typical test commands (examples only): `npm test`, `npx vitest run [path]`, `pytest`, `go test ./...`.

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Bug fixed | Original symptom no longer reproduces | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | `git diff` shows expected changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing alone |

## Red Flags — STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit/push/PR without verification
- Trusting subagent success reports without checking diff
- Relying on partial verification

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34 runs, 0 failures] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Agent delegation:**
```
✅ Agent reports success → Check git diff → Run tests → Report actual state
❌ Trust agent report
```

## When To Apply

**ALWAYS before:**
- ANY success/completion claims
- Committing, PR creation, task completion
- Moving to next task in a plan
- Handing off to the user

## Related Skills

- **systematic-debugging** — Before claiming a bug is fixed
- **git-commit** — After verification passes, before committing
- **self-review** (`~/.agents/skills/global/self-review`) — Pre-commit quality pass