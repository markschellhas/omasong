---
name: git-commit
description: Create conventional commit messages. Use when committing changes or writing commit messages.
user-invocable: true
---

# Git Commit

Use conventional commits. Scope by package or app when changes are isolated.

## Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

## Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring, no behavior change |
| `perf` | Performance improvement |
| `test` | Adding/updating tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |
| `revert` | Reverting previous commit |

## Scopes

Use the top-level package or app directory as scope when changes are isolated there. Infer names from the repo layout (directory names, package.json `name` fields, workspace packages).

Omit scope, or use a feature name, for cross-cutting changes.

## Rules

### Subject Line
- Max 50 characters
- Imperative mood ("add" not "added")
- No period at end
- Lowercase

### Body (optional)
- Wrap at 72 characters
- Explain what and why, not how
- Separate from subject with blank line

### Footer (optional)
- Reference issues: `Closes #123`, `Fixes #456`
- Breaking changes: `BREAKING CHANGE: description`

## Examples

```
feat(api): add bulk export for reports
```

```
fix(web): handle null response from the export API

The endpoint occasionally returns null when the job is still
processing. Added polling with timeout instead of crashing.

Fixes #789
```

```
docs: add implementation plan for archive endpoint
```

## Workflow

1. Run **verification-before-completion** — tests must pass before committing
2. Stage only files relevant to this change — avoid drive-by commits
3. Write message following format above
4. One logical change per commit when executing plans

## Commands

```bash
git add <files>
git commit -m "feat(api): description"

# Amend last commit (only if not pushed)
git commit --amend
```
