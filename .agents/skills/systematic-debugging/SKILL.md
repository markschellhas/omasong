---
name: systematic-debugging
description: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes. Enforces root-cause investigation before any code change.
user-invocable: true
---

# Systematic Debugging

## Overview

Random fixes waste time and create new bugs. Quick patches mask underlying issues.

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

**Violating the letter of this process is violating the spirit of debugging.**

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

If you haven't completed Phase 1, you cannot propose fixes.

**REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.

## When to Use

Use for ANY technical issue:
- Test failures
- Bugs in production
- Unexpected behavior
- Performance problems
- Build failures
- Integration issues across packages or services

**Use this ESPECIALLY when:**
- Under time pressure (emergencies make guessing tempting)
- "Just one quick fix" seems obvious
- You've already tried multiple fixes
- Previous fix didn't work
- You don't fully understand the issue

## The Four Phases

You MUST complete each phase before proceeding to the next.

### Phase 1: Root Cause Investigation

**BEFORE attempting ANY fix:**

1. **Read Error Messages Carefully**
   - Don't skip past errors or warnings
   - Read stack traces completely
   - Note line numbers, file paths, error codes

2. **Reproduce Consistently**
   - Can you trigger it reliably?
   - What are the exact steps?
   - Does it happen every time?
   - If not reproducible → gather more data, don't guess

3. **Check Recent Changes**
   - `git diff`, recent commits
   - New dependencies, config changes
   - Environmental differences

4. **Gather Evidence in Multi-Component Systems**

   **WHEN the bug spans multiple layers (e.g. client → API → database → background job):**

   **BEFORE proposing fixes, add diagnostic instrumentation at each boundary:**
   - Log what data enters each component
   - Log what data exits each component
   - Verify environment/config propagation
   - Check state at each layer

   Run once to gather evidence showing WHERE it breaks, THEN investigate the failing component.

5. **Trace Data Flow**

   When error is deep in call stack:
   - Where does the bad value originate?
   - What called this with the bad value?
   - Keep tracing up until you find the source
   - Fix at source, not at symptom

### Phase 2: Pattern Analysis

1. **Find Working Examples** — Locate similar working code nearby in this codebase
2. **Compare Against References** — Read reference implementation completely
3. **Identify Differences** — List every difference, however small
4. **Understand Dependencies** — Config, env, assumptions, contracts between packages or services

### Phase 3: Hypothesis and Testing

1. **Form Single Hypothesis** — "I think X is the root cause because Y"
2. **Test Minimally** — Smallest possible change, one variable at a time
3. **Verify Before Continuing** — Worked? → Phase 4. Didn't? → New hypothesis
4. **When You Don't Know** — Say so. Research more. Ask for help.

### Phase 4: Implementation

1. **Create Failing Test Case** — Simplest reproduction; automated test when possible
2. **Implement Single Fix** — Address root cause only; no bundled refactoring
3. **Verify Fix** — Run verification per `verification-before-completion` skill
4. **If Fix Doesn't Work** — After 3 failed attempts, question the architecture with the user

## Verification Commands

Use the test command this repo actually runs for the affected area (CI, package scripts, Makefile, README, AGENTS.md). Examples: `npm test`, `npx vitest run [path]`, `pytest`, `go test ./...`.

## Red Flags — STOP and Follow Process

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "It's probably X, let me fix that"
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)
- Each fix reveals new problem in different place

**ALL of these mean: STOP. Return to Phase 1.**

## Related Skills

- **verification-before-completion** — Verify fix with fresh command output before claiming success
- **dispatching-parallel-agents** — When multiple independent test files/subsystems fail
- **writing-plans** — When the fix requires a multi-step implementation