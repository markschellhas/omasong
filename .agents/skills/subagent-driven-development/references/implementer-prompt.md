# Implementer Subagent Prompt Template

Use when dispatching an implementer subagent via the environment's Task / subagent tool.

```
Task tool (general-purpose):
  description: "Implement Task N: [task name]"
  prompt: |
    You are implementing Task N: [task name] in this codebase.

    ## Task Description

    [FULL TEXT of task from plan — paste here, don't make subagent read file]

    ## Context

    [Scene-setting: where this fits, dependencies, architectural context]
    [Feature map summary if applicable]
    [Affected packages / directories]

    ## Before You Begin

    If you have questions about requirements, approach, dependencies, or anything
    unclear in the task description — **ask them now** before starting work.

    ## Your Job

    Once clear on requirements:
    1. Implement exactly what the task specifies
    2. Write tests (TDD if task says to)
    3. Verify with this project's test command
    4. Commit using conventional commits (feat/fix/test with package scope when isolated)
    5. Self-review (see below)
    6. Report back

    Work from: [directory or worktree path]

    ## Test Commands

    [Paste the exact command from the plan / CI / package scripts for this task]

    ## Before Reporting Back: Self-Review

    **Completeness:** Did I implement everything? Edge cases handled?
    **Quality:** Clear names, clean code, follows existing patterns?
    **Discipline:** YAGNI — only what was requested?
    **Testing:** Tests verify behavior, not just mocks?

    Fix issues found during self-review before reporting.

    ## Report Format

    When done, report:
    - What you implemented
    - Test results (exact command + output summary)
    - Files changed
    - Commit SHA
    - Self-review findings (if any)
    - Any issues or concerns
```