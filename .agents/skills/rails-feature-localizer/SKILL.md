---
name: rails-feature-localizer
description: "Use this skill to localize a Rails feature or file by extracting hardcoded text and implementing i18n translation strings across locale files. Trigger this skill when working on Rails views, components, or any files containing hardcoded user-facing text that needs internationalization. Also trigger when the user says 'localize', 'i18n', 'translate this file', 'add translations', or mentions locale files. Use this even if the user just finished building a feature and hasn't explicitly asked for localization — if there's hardcoded text in Rails views, this skill applies."
---

# Feature Localizer

Localize Rails features by extracting hardcoded user-facing text, replacing it with i18n calls, and maintaining consistent translations across all locale files.

## Scope

Determine what to localize based on the user's request:
- Single file referenced → localize that file only
- Multiple files or a feature name → localize all relevant files
- Ambiguous → ask the user to clarify

## What to Localize

Scan for all hardcoded user-facing text:
- Headers, titles, descriptions, body text
- Form labels, placeholders, button text, CTAs
- Error and validation messages
- Navigation items, tooltips, help text
- Empty state messages

Leave alone: code comments, CSS classes, HTML IDs, internal identifiers, and dynamic/user-generated content.

## Workflow

1. **Read the target file(s)** — identify every hardcoded user-facing string
2. **Find existing locale files** — typically `config/locales/*.yml` at the Rails root (repo root or a subdirectory). Read them to understand conventions, nesting, and key naming already in use. Do not assume which locales exist.
3. **Check for reusable keys** — if a translation already exists with the right value, reuse it
4. **Plan your key structure** — follow whatever nesting pattern the existing locale files use (e.g., organized by feature, by controller path, etc.)
5. **Replace hardcoded strings** with i18n calls in the source files
6. **Update every locale file this app already maintains** with new keys and accurate translations
7. **Verify** every new key exists in all of those locale files

## i18n Call Conventions

- ERB views: `t('.relative_key')` (preferred) or `t('full.path.to.key')`
- Ruby code: `I18n.t('full.path.to.key')`
- Haml: `= t('.key')`
- Interpolation: `t('.greeting', name: user.name)` → `"Hello, %{name}!"`
- HTML content: use `_html` suffix → `t('.description_html')`
- Pluralization: use Rails pluralization conventions when text varies by count
- Form labels: replace hardcoded label text in form helpers — `f.label :email, "Email address"` → `f.label :email, t('.email')`, and `label_tag :name, "Full name"` → `label_tag :name, t('.name')`

Prefer relative keys (`.key`) in views when following Rails view-path conventions.

## Locale File Rules

- **Update every locale this app already has** in the same change — never add a key to only one file
- **The default locale** (usually English, but follow `config.i18n.default_locale` / existing files) is the source of truth; other locales must have real, accurate translations (never placeholders or copies of the default)
- **Match existing conventions exactly** — indentation (2 spaces), quoting style, nesting depth, key naming
- **Only add keys** — never modify or remove existing keys unless explicitly asked
- **Group new keys** near related existing keys
- **Verify key paths** — the nesting in the YAML must exactly match the i18n call path in the source file
