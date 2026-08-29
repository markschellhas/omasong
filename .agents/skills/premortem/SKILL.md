---
name: premortem
description: Pre-mortem analysis that imagines a plan has failed, then works backward to identify causes and preventions. Use before launches, major decisions, or risky initiatives to surface hidden risks.
user-invocable: true
argument-hint: "[initiative or feature to analyze]"
---

# Pre-Mortem Analysis

Imagine the plan has completely failed, then work backward to identify what went wrong and how to prevent it.

**REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.

## When to Use

- Before shipping a major feature
- Before changes that span multiple packages or services
- After writing a PRD or implementation plan
- Before production deploys
- When the team feels overconfident

## Context

Ground risks in this codebase's actual architecture (from feature-map and inspection), not generic checklists. Look for:

- Contract breaks between services or clients
- Shared data stores queried from multiple places
- Async jobs and other work that fails out of band
- i18n, permissions, and other easy-to-forget surfaces
- Single points of failure (auth, primary database, object storage, deploy path)

## Instructions

Set the scene: "It's [timeframe] in the future. This initiative was a complete disaster. Looking back, what happened?"

Generate failure scenarios without filtering for likelihood — get everything on the table first, then prioritize.

## Output Format

**The Plan**
Summarize what's being attempted and the success criteria.

**Time Jump**
"It's [X months] later. This has failed completely. The outcome: [describe the disaster vividly]."

**What Went Wrong**

Generate 8–12 plausible failure causes:

| Category | Failure Mode | How It Played Out |
|----------|--------------|-------------------|
| Execution | [What failed] | [The story of how] |
| External | [What failed] | [The story of how] |
| People | [What failed] | [The story of how] |
| Technical | [What failed] | [The story of how] |
| Assumptions | [What failed] | [The story of how] |

**Risk Prioritization**

| Failure Mode | Likelihood | Impact | Priority |
|--------------|------------|--------|----------|
| ... | High/Med/Low | High/Med/Low | 1-5 |

**Top 3 Risks & Mitigations**

For each top risk:
- **Risk**: [Description]
- **Early Warning Signs**: What would indicate this is happening?
- **Prevention**: How to reduce likelihood
- **Mitigation**: How to reduce impact if it occurs
- **Owner**: Who's responsible for watching this?

**Pre-Mortem Insights**
What did this exercise reveal that wasn't obvious before?

**Revised Confidence**
After this analysis, how confident are you in success? What would increase confidence?

## Guidelines

- Be vivid and specific — "login crashed for users in a secondary locale" not "something went wrong"
- Include uncomfortable possibilities (key person leaves, a breaking API change ships)
- Don't filter for "that won't happen"
- Look for single points of failure
- Assign real owners to mitigations

## Related Skills

- **product-requirements** — Upstream planning
- **writing-plans** — Turn mitigations into implementation tasks
- **harden** — Edge cases and error states for UI
- **rice** — Prioritize which risks to address first
