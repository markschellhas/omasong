---
name: dispatching-parallel-agents
description: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies. Dispatches one subagent per problem domain.
user-invocable: true
---

# Dispatching Parallel Agents

When you have multiple unrelated failures (different test files, different subsystems, different bugs), investigating them sequentially wastes time. Each investigation is independent and can happen in parallel.

**Core principle:** Dispatch one agent per independent problem domain. Let them work concurrently.

## When to Use

**Use when:**
- 3+ test files failing with different root causes
- Multiple subsystems broken independently
- Each problem can be understood without context from others
- No shared state between investigations
- Cross-package work where changes are independent

**Don't use when:**
- Failures are related (fix one might fix others)
- Need to understand full system state
- Agents would edit the same files
- Exploratory debugging — you don't know what's broken yet

## The Pattern

### 1. Identify Independent Domains

Group failures by what's broken, for example:
- `src/lib/invoiceTotal.test.ts` — calculator
- `src/api/exports.test.ts` — API client
- `src/components/ExportButton.test.tsx` — UI component

Each domain is independent if fixing one doesn't require changes in the other.

### 2. Create Focused Agent Tasks

Each agent gets:
- **Specific scope:** One test file, subsystem, or package
- **Clear goal:** Make these tests pass / fix this bug
- **Constraints:** Don't change unrelated code
- **Context:** Feature-map output, error messages, relevant file paths
- **Expected output:** Summary of root cause and changes

### 3. Dispatch in Parallel

Use this environment's subagent / Task tool — launch multiple subagents in a single message:

```
Task("Fix invoiceTotal.test.ts failures")
Task("Fix exports.test.ts failures")
Task("Fix ExportButton.test.tsx failures")
```

All three run concurrently.

### 4. Review and Integrate

When agents return:
- Read each summary
- Check for conflicting file edits (`git diff`)
- Run full test suite per **verification-before-completion**
- Integrate all changes

## Agent Prompt Structure

Good prompts are:
1. **Focused** — One clear problem domain
2. **Self-contained** — Error messages, file paths, feature-map context
3. **Specific about output** — Root cause + files changed + test results

```markdown
Fix the 3 failing tests in src/lib/invoiceTotal.test.ts:

1. "calculates total for a complete invoice" — expected 0.85, received undefined
2. "handles missing line items" — TypeError: Cannot read properties of undefined (reading 'map')
3. "queues export job" — expected 1 call, received 0

Context:
- Feature map: ./bin/feature-map invoicing
- Use systematic-debugging: root cause before fixes
- Tests: npx vitest run src/lib/invoiceTotal.test.ts

Constraints:
- Do NOT change unrelated modules
- Follow existing patterns in the surrounding code

Return: Summary of root cause, files changed, test output.
```

## Common Mistakes

| Bad | Good |
|-----|------|
| "Fix all the tests" | "Fix invoiceTotal.test.ts" |
| "Fix the race condition" | Paste error messages and test names |
| No constraints | "Do NOT change production code outside scope" |
| "Fix it" | "Return summary of root cause and changes" |

## Verification

After agents return:
1. Review each summary
2. Check for conflicts — did agents edit same code?
3. Run the full suite for the affected area
4. Spot check — agents can make systematic errors

## Parallel vs sequential

**Parallel** (when the contract between areas is stable):
- Agent 1 → API + tests
- Agent 2 → client consuming that endpoint

**Sequential** (when the contract is changing):
- Agent 1 ships the API first
- Agent 2 updates the client after

## Related Skills

- **systematic-debugging** — Each agent should follow root-cause-first
- **verification-before-completion** — Full suite after integration
- **subagent-driven-development** — For sequential plan execution (not parallel)
- **using-git-worktrees** — Isolate parallel work in separate worktrees if needed
