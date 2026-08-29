---
name: rice
description: RICE prioritization scoring initiatives by Reach, Impact, Confidence, and Effort. Use for feature prioritization, roadmap planning, or when comparing initiatives objectively.
user-invocable: true
argument-hint: "[initiatives to compare]"
---

# RICE Prioritization Scoring

Score and rank initiatives using Reach, Impact, Confidence, and Effort to make prioritization decisions more objective.

**REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.

## When to Use

- Choosing between multiple features for a sprint
- Comparing items in a PRD backlog
- Roadmap planning across packages or apps
- When stakeholders disagree on priority

## Instructions

For each initiative, estimate the four RICE factors, calculate the score, and rank them. Be explicit about assumptions.

**Formula:** `RICE = (Reach × Impact × Confidence) / Effort`

## Output Format

**Context**
What are we prioritizing? What's the time horizon for Reach? (e.g. "users affected per quarter")

**Factor Definitions**
- **Reach**: [Define for this context]
- **Impact**: [Define for this context]
- **Effort**: [Define unit — engineer-days or t-shirt sizes converted to numbers]

**Scoring Table**

| Initiative | Reach | Impact | Confidence | Effort | RICE Score |
|------------|-------|--------|------------|--------|------------|
| [Name A] | [#] | [0.25-3] | [%] | [#] | [calculated] |
| [Name B] | [#] | [0.25-3] | [%] | [#] | [calculated] |

**Ranked Results**

1. **[Highest score]** — RICE: X
2. **[Second]** — RICE: X

**Detailed Breakdown**

For each initiative:

### [Initiative Name]
- **Reach**: [X] — [Assumption]
- **Impact**: [X] — [Reasoning]
- **Confidence**: [X%] — [What would increase confidence?]
- **Effort**: [X] — [What's included? Note cross-package work]
- **RICE Score**: (R × I × C) / E = [score]

**Sensitivity Analysis**
Which scores change significantly if assumptions are wrong?

**Recommendation**
> [What to prioritize and why, including caveats]

**What RICE Doesn't Capture**
- Strategic alignment
- Dependencies (e.g. a client blocked on an API change)
- Team capability gaps
- Technical risk (use **premortem** for that)
- Design debt (use **audit** / **critique**)

## Scoring Guide

**Impact Scale**

| Score | Meaning |
|-------|---------|
| 3 | Massive — core value prop |
| 2 | High — significant improvement |
| 1 | Medium — noticeable improvement |
| 0.5 | Low — minor enhancement |
| 0.25 | Minimal — nice to have |

**Confidence Scale**

| Score | Meaning |
|-------|---------|
| 100% | High — have data |
| 80% | Medium — reasonable estimate |
| 50% | Low — mostly guessing |

## Notes

- Effort should include all affected packages (backends, clients, i18n, tests)
- Reach for one audience may not equal reach for another — score separately if audiences differ
- High-effort cross-package changes may rank lower even with high impact

## Related Skills

- **product-requirements** — Detailed spec for top-ranked item
- **writing-plans** — Implementation plan for chosen initiative
- **premortem** — Risk analysis on high-impact picks
