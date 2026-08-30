# PRD: Song Library

**Status:** Draft
**Owner:** songwriter

---

## Overview

Users can name the current song, save its structure to a durable on-disk library, and reopen a saved song later. Persistence follows the Radio Atlas pattern: library data lives under `$XDG_DATA_HOME` (default `~/.local/share/songwriter/`) so it survives plugin removal, while the working session continues to autosave under `~/.local/state/omarchy/songwriter/song.json`.

## Goals / Non-Goals

**Goals:**
1. Editable song title on the transport row (left).
2. Save upserts the current document into the library by stable `id`.
3. Open lists saved songs and loads one into the editor.
4. Library file uses flock + validation + atomic replace like `radio-state`.
5. Transport/BPM controls move to the right of the same transport row.

**Non-Goals:**
- Cloud sync, export/import ZIP, or sharing.
- Autosave into the library on every edit (library write is explicit Save only).
- Folder hierarchy, tags, or search beyond a simple open list.
- Changing agent-api snapshot paths or contracts.

## Current Implementation

Session song persists via `write-json.py` to `~/.local/state/omarchy/songwriter/song.json` (`Songwriter.qml` `persistNow`). Documents have `bpm`, `keyIndex`, `sections` (`js/Song.js`); no song-level title or library id. Transport is a single left-aligned row of Play/Loop/BPM/beat (`Transport.qml`). Feature maps: `song_structure`, `playback`. No `song_library` map existed before this work.

## Proposed Implementation

- Add `title` and `id` on the song document (normalize + default).
- Split `Transport.qml` into left (title field, Save, Open) and right (existing transport/BPM).
- Add `song-library` helper (bash, Radio Atlas–style) owning `library.json` under XDG data home.
- QML stages the save payload under `$XDG_RUNTIME_DIR/omarchy-songwriter/`, then runs `song-library save|delete|get`.
- Open menu lists library titles (reuse SongStructure-style menu overlay pattern).

## Technical Details

- Library schema: `{ "songs": [ { "id", "title", "updatedAt", "song" } ] }` with caps (count + bytes) and jq validation.
- Session `song.json` keeps including `title`/`id` so reopen of the app restores the working title.
- Save mints a UUID when `id` is missing; later saves upsert by `id`.
- Load replaces `root.song` via `seedSong`, stops playback, refreshes piano, persists session.
- Tests: helper CLI via `tests/run.py`; Song.js title/id normalize in `tests/js_tests.js`.
- Feature map: `.features/song_library.yaml`; update `playback` / `song_structure` notes for title + library coupling.

## Effort Estimates

- Library helper + tests: **M**
- Song model (`title`/`id`) + tests: **S**
- Transport UI split + Save/Open wiring: **M**
- Feature maps / docs: **S**

## Open Questions

- None blocking: delete-from-open-menu is in scope; “Save as new copy” is out (YAGNI).

## Related Docs

- `.features/song_library.yaml`
- `.features/song_structure.yaml`
- `.features/playback.yaml`
- Reference: `akshar.radio-atlas` `radio-state` + `~/.local/share/radio-atlas/state.json`
