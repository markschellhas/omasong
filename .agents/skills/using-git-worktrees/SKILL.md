---
name: using-git-worktrees
description: Use when starting feature work that needs isolation from current workspace or before executing implementation plans. Creates isolated git worktrees with safety verification.
user-invocable: true
argument-hint: "[branch name]"
---

# Using Git Worktrees

Git worktrees create isolated workspaces sharing the same repository, allowing work on multiple branches simultaneously without switching.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

**Announce at start:** "I'm using the using-git-worktrees skill to set up an isolated workspace."

## Directory Selection

Follow this priority order:

### 1. Check Existing Directories

```bash
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

**If found:** Use that directory. If both exist, `.worktrees` wins.

### 2. Default

If neither exists, create `.worktrees/` (project-local, hidden).

### 3. Ask User

Only if there's a reason to use a global location outside the repo.

## Safety Verification

**MUST verify directory is ignored before creating a project-local worktree:**

```bash
git check-ignore -q .worktrees 2>/dev/null
```

**If NOT ignored:**

1. Add `.worktrees/` to `.gitignore`
2. Commit the change
3. Proceed with worktree creation

**Why critical:** Prevents accidentally committing worktree contents.

## Creation Steps

### 1. Detect Project Name

```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

### 2. Create Worktree

```bash
BRANCH_NAME="feature/<slug>"
path=".worktrees/$BRANCH_NAME"

git worktree add "$path" -b "$BRANCH_NAME"
cd "$path"
```

### 3. Run Project Setup

Auto-detect from lockfiles, `bin/setup`, Makefile, README, or AGENTS.md. Run only setup relevant to the feature — don't install everything blindly.

Examples of what you might find (use what this repo actually has):

```bash
# Project-provided setup
if [ -x bin/setup ]; then
  ./bin/setup
fi

# Node — prefer the lockfile's package manager
if [ -f pnpm-lock.yaml ]; then pnpm install
elif [ -f yarn.lock ]; then yarn install
elif [ -f bun.lockb ] || [ -f bun.lock ]; then bun install
elif [ -f package-lock.json ] || [ -f package.json ]; then npm install
fi

# Ruby
if [ -f Gemfile ]; then
  bundle install
fi

# Python
if [ -f uv.lock ]; then uv sync
elif [ -f poetry.lock ]; then poetry install
elif [ -f pyproject.toml ] || [ -f requirements.txt ]; then
  # follow the project's documented install path
  true
fi

# Flutter / Dart
if [ -f pubspec.yaml ]; then
  flutter pub get
fi

# Go / Rust
if [ -f go.mod ]; then go mod download; fi
if [ -f Cargo.toml ]; then cargo fetch; fi
```

If the repo is a monorepo, run setup only in the packages this feature touches. Repeat the same detection inside those directories.

### 4. Verify Clean Baseline

Run tests for the affected package using this project's real test command (CI, package scripts, Makefile, README).

**If tests fail:** Report failures, ask whether to proceed or investigate.

**If tests pass:** Report ready.

### 5. Report Location

```
Worktree ready at <full-path>
Branch: feature/<slug>
Tests passing (<N> runs, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| Neither exists | Create `.worktrees/`, add to `.gitignore` |
| Directory not ignored | Add to `.gitignore` + commit |
| Tests fail during baseline | Report failures + ask |
| Plan exists | Load `docs/plans/<file>.md` in worktree |

## Red Flags

**Never:**
- Create worktree without verifying it's ignored
- Skip baseline test verification
- Proceed with failing tests without asking

**Always:**
- Verify directory is ignored for project-local
- Run relevant setup and tests
- Use descriptive branch names: `feature/<slug>`

## Cleanup

When work is complete:
```bash
cd <main-workspace>
git worktree remove .worktrees/feature/<slug>
git branch -d feature/<slug>   # if merged
```

## Related Skills

- **writing-plans** — Plans saved to `docs/plans/`; implement in worktree
- **subagent-driven-development** — Execute plan tasks in isolated worktree
- **verification-before-completion** — Baseline and final verification
- **git-commit** — Commits happen inside the worktree branch
