# Code Quality Reviewer Prompt Template

Use when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Only dispatch after spec compliance review passes.**

```
Task tool (code-reviewer):
  description: "Review code quality for Task N"
  prompt: |
    Review the code quality of this task's implementation.

    ## What Was Implemented

    [From implementer's report]

    ## Plan Requirements

    Task N from [plan-file]

    ## Commits

    BASE_SHA: [commit before task]
    HEAD_SHA: [current commit]

    ## Review For

    - Code clarity and naming
    - Test coverage and quality
    - Follows existing patterns in this codebase
    - No unnecessary complexity (YAGNI)
    - Error handling appropriate for this stack
    - UI: match this repo's existing component and styling conventions
    - Security: no exposed secrets, proper auth checks

    ## Return Format

    **Strengths:** [what's good]
    **Issues:**
    - Critical: [must fix]
    - Important: [should fix]
    - Minor: [nice to fix]
    **Assessment:** Approved / Needs changes
```