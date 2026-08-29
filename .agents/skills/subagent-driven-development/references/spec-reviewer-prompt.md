# Spec Compliance Reviewer Prompt Template

Use when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

**Dispatch after implementer reports completion, before code quality review.**

```
Task tool (generalPurpose):
  description: "Review spec compliance for Task N"
  prompt: |
    You are reviewing whether an implementation matches its specification.

    ## What Was Requested

    [FULL TEXT of task requirements]

    ## What Implementer Claims They Built

    [From implementer's report]

    ## CRITICAL: Do Not Trust the Report

    Verify everything independently by reading the actual code.

    **DO NOT:**
    - Take their word for what they implemented
    - Trust claims about completeness

    **DO:**
    - Read the actual code they wrote
    - Compare implementation to requirements line by line
    - Check for missing pieces and extra features

    ## Your Job

    Read the implementation and verify:

    **Missing requirements:**
    - Did they implement everything requested?
    - Requirements skipped or missed?

    **Extra/unneeded work:**
    - Features not requested?
    - Over-engineering?

    **Misunderstandings:**
    - Wrong problem solved?
    - Right feature, wrong approach?

    Report:
    - ✅ Spec compliant (everything matches after code inspection)
    - ❌ Issues found: [list with file:line references]
```