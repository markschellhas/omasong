---
name: product-requirements
description: "Create PRDs for any feature or project. Store in @docs/ folder with filename prefix 'prd-'."
---

# Product Requirements Document Writer

Create Product Requirement Documents (PRDs) for features or projects in this codebase. Follow this workflow every time — do not skip steps.

**REQUIRED SUB-SKILL:** Use `feature-map` before proceeding.

## Step 1: Choose filename and location

- **Directory:** `docs/prds/` only — not elsewhere in the repo.
- **Prefix:** filename must start with exactly `prd-`.
- **Slug:** derive a kebab-case slug from the feature or project title (e.g. `export` → `prd-export.md`, `Dashboard States` → `prd-dashboard-states.md`).
- **Full path example:** `docs/prds/prd-bulk-export.md`

Do not edit, move, or reformat existing PRD files. Create a new file only.

## Step 2: Write the PRD

Use the Write tool to create the file at the chosen `docs/prd-<slug>.md` path.

Every PRD must use **precisely** these top-level sections in this order:

```markdown
# PRD: <Title>

**Status:** Draft
**Owner:** <team or role>

---

## Overview

What the feature/project is and why it matters. Summarize the problem, user need, and expected outcome. Ground this in feature-map research where applicable.

## Goals / Non-Goals

**Goals:** numbered list of measurable outcomes.

**Non-Goals:** explicit scope boundaries — what this PRD does not cover.

## Current Implementation

Describe how the feature works today. Include entry points, key files, and behavior drawn from feature-map output and codebase inspection.

*If this is greenfield with no existing implementation, write: "No current implementation — greenfield feature."*

## Proposed Implementation

The planned solution: user-facing changes, API/route changes, data model changes, and cross-package impact if this is a monorepo.

## Technical Details

Concrete implementation notes: controllers, models, jobs, frontend surfaces, migrations, feature flags, i18n, analytics, and dependencies.

## Effort Estimates

Break down by workstream or phase using **only** these relative effort sizes: **S** (small), **M** (medium), **L** (large). Example: API: M, Client: S.

These are relative effort, not calendar time. Never write days, hours, weeks, sprints, or any schedule/duration.

## Open Questions

Unresolved decisions, risks, or items needing stakeholder input.

## Related Docs

Links to feature maps (`.features/<name>.yaml`), existing PRDs, project docs (AGENTS.md, README), and other relevant docs.
```

## Step 3: Quality checks before finishing

1. Filename starts with `prd-` and lives under `docs/`.
2. All eight sections appear in the order above.
3. Content reflects feature-map research (flows, entry points, business rules) — not guesses.
4. Scope stays within the user's request; do not expand into review loops, persona orchestration, or feature-map authoring.
5. Effort Estimates use only S / M / L (small / medium / large). No calendar time (days, hours, weeks, sprints) anywhere in the PRD.

## What this skill does not do

- Edit or relocate existing PRDs in `docs/` or `docs/prds/` (use **ship-plan** to set Status Shipped and move finished PRDs + plans to `docs/shipped/`)
- Create or modify `.features/*.yaml` files
- Run multi-pass review/revise loops or subagent orchestration
- Place PRDs outside `docs/` or use filenames without the `prd-` prefix
- Express effort as calendar time (days, hours, weeks, sprints) — use S / M / L only
