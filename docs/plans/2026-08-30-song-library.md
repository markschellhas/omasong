# Song Library Implementation Plan

> **For agent:** REQUIRED SUB-SKILL: Use subagent-driven-development to implement this plan task-by-task.
> Update each task's **Status** as work advances (not only at the end). Progress bar counts only `done` tasks.
> On resume: read **Progress** + each task's **Status** / **Resume** — do not re-do completed phases.

**Goal:** Let users name, save, and reopen song structures in an XDG data-home library (Radio Atlas–style), with title/Save/Open on the left of the transport row and Play/Loop/BPM on the right.

**Architecture:** Session autosave stays at `~/.local/state/omarchy/songwriter/song.json`. The durable library is `$XDG_DATA_HOME/songwriter/library.json` (else `~/.local/share/songwriter/library.json`), mutated only by a locked `song-library` helper. QML stages save payloads under `$XDG_RUNTIME_DIR/omarchy-songwriter/` then runs the helper via `Process`, mirroring Radio Atlas favorites.

**Areas affected:** `Transport.qml`, `Songwriter.qml`, `js/Song.js`, new `song-library`, tests, `.features/`

**Tech Stack:** QML/Quickshell, bash + jq + flock, Node JS unit harness, Python `tests/run.py`

**Feature map:** `.features/song_library.yaml`

**PRD:** `docs/prds/prd-song-library.md`

## Progress

**Status:** `████████████████████` 7/7 done (100%) · 0 in flight

| # | Task | Status | Next |
|---|------|--------|------|
| 1 | Feature map polish + related notes | `done` | — |
| 2 | Song `title`/`id` in Song.js + tests | `done` | — |
| 3 | `song-library` helper + Python tests | `done` | — |
| 4 | Transport row split (title / Save / Open / right transport) | `done` | — |
| 5 | Wire Save/Open/delete in Songwriter.qml | `done` | — |
| 6 | End-to-end verification + map check | `done` | — |
| 7 | Commit feature on branch | `done` | — |

---

### [x] Task 1: Feature map polish + related notes

**Status:** `done`
**Resume:** Complete
**Commits:** c60189d

**Files:**
- Modify: `.features/song_library.yaml` (already scaffolded)
- Modify: `.features/playback.yaml`
- Modify: `.features/song_structure.yaml`

**Step 1:** Ensure `song_library.yaml` matches authoring density (already written in worktree).

**Step 2:** Patch `playback.yaml` notes to mention transport left cluster is title/library; right is play/BPM.

**Step 3:** Patch `song_structure.yaml` notes: session path unchanged; named library is separate (`song_library`).

**Step 4:** Run:
```bash
./bin/feature-map validate
./bin/feature-map check
```
Expected: no errors.

**Step 5:** Commit
```bash
git add .features/song_library.yaml .features/playback.yaml .features/song_structure.yaml docs/prds/prd-song-library.md
git commit -m "$(cat <<'EOF'
docs(song_library): add PRD and feature map for saved songs

EOF
)"
```

---

### [x] Task 2: Song `title`/`id` in Song.js + tests

**Status:** `done`
**Resume:** Complete
**Commits:** 3e1c786

**Files:**
- Modify: `js/Song.js`
- Modify: `tests/js_tests.js`

**Step 1: Failing tests** in `tests/js_tests.js`:
- `defaultSong()` has `title: "Untitled"` and empty/`null` id handled as `""`
- `normalizeSong` trims title, clamps length (e.g. 80 chars), preserves non-empty id string matching uuid-ish or any non-empty trimmed id ≤ 64
- Round-trip: normalize keeps title/id through cloneSong

**Step 2:** Run `python3 tests/run.py` — expect JS assert failures.

**Step 3: Implement** in `js/Song.js`:
```javascript
var MAX_TITLE_LEN = 80
var MAX_ID_LEN = 64

function normalizeTitle(raw) {
  var t = typeof raw === "string" ? raw.trim() : ""
  if (!t) return "Untitled"
  if (t.length > MAX_TITLE_LEN) t = t.slice(0, MAX_TITLE_LEN)
  return t
}

function normalizeId(raw) {
  if (typeof raw !== "string") return ""
  var id = raw.trim()
  if (!id || id.length > MAX_ID_LEN) return ""
  return id
}
```
Wire into `defaultSong` / `normalizeSong`. Do not invent UUIDs in Song.js — QML/helper mints on first Save.

**Step 4:** Re-run `python3 tests/run.py` — JS ok.

**Step 5:** Commit
```bash
git add js/Song.js tests/js_tests.js
git commit -m "$(cat <<'EOF'
feat(song): add title and id fields on song documents

EOF
)"
```

---

### [x] Task 3: `song-library` helper + Python tests

**Status:** `done`
**Resume:** Complete
**Commits:** 1db22f9, 71f6853

**Files:**
- Create: `song-library` (executable bash, modeled on `akshar.radio-atlas/radio-state`)
- Modify: `tests/run.py`

**Contract:**

| Env | Role |
|-----|------|
| `$XDG_DATA_HOME/songwriter/` or `~/.local/share/songwriter/` | durable `library.json` + `library.lock` |
| `$XDG_RUNTIME_DIR/omarchy-songwriter/` | staging (`save-selection.json`) |

Default empty library: `{"songs":[]}`

Validation (refuse overwrite if invalid — exit 4):
- single JSON object
- `songs` array length ≤ 100
- each entry: `id` string, `title` string, `updatedAt` number, `song` object with `sections` array
- file ≤ 4MiB

Actions:
- `get` — print library.json
- `save` — read staged song object from `$XDG_RUNTIME_DIR/omarchy-songwriter/save-selection.json` (full library entry or `{id,title,song}`); upsert by `id`; set `updatedAt` to epoch seconds; require non-empty id; move to front; cap 100
- `delete <id>` — remove matching entry
- Always print final library JSON on stdout (like radio-state)

Use `flock`, `mktemp` + `mv`, `umask 077`, `install -d -m 700`.

**Tests** in `tests/run.py` (tmpdir + env overrides):
```python
env = {**os.environ, "XDG_DATA_HOME": str(data), "XDG_RUNTIME_DIR": str(runtime)}
```
- get creates empty library
- save upserts then updates title
- delete removes
- corrupt library → exit 4 on next write attempt after detecting invalid (match radio-state)

**Step 1:** Write failing test harness calls.
**Step 2:** Implement `song-library`.
**Step 3:** `chmod +x song-library` and run `python3 tests/run.py`.
**Step 4:** Commit
```bash
git add song-library tests/run.py
git commit -m "$(cat <<'EOF'
feat(song_library): add XDG data-home library helper

EOF
)"
```

---

### [x] Task 4: Transport row split

**Status:** `done`
**Resume:** Complete
**Commits:** d305f2d

**Files:**
- Modify: `Transport.qml`

**Layout (one row, two clusters):**

```
[ Title TextInput ] [Save] [Open]     ……     [Play] [Loop] | BPM − [n] + ● bar:beat [status]
```

Use a full-width `Item` with:
- Left `Row`: title field (~`Style.space(220)`), Save button, Open button
- Right `Row` anchored right: existing Play/Loop/BPM/beat/status (move current controls here)

**New API:**
```qml
property string songTitle: "Untitled"
signal titleEdited(string value)
signal saveRequested
signal openRequested
```

Title `TextInput`: commit on `editingFinished` / Enter; when not focused, bind display to `songTitle`. Match existing BPM field chrome (border, fonts from Style).

Save/Open: `Button` with text `"Save"` / `"Open"` (icons optional; prefer text for clarity). `tooltipText` set. Emit signals; do not call library from Transport.

**Step 1:** Implement layout.
**Step 2:** Visual smoke — open overlay manually if linked; otherwise rely on Task 5 wiring.
**Step 3:** Commit
```bash
git add Transport.qml
git commit -m "$(cat <<'EOF'
feat(transport): split title/library controls from playback

EOF
)"
```

---

### [x] Task 5: Wire Save/Open/delete in Songwriter.qml

**Status:** `done`
**Resume:** Complete
**Commits:** 7f194e1, 26aa4cf

**Files:**
- Modify: `Songwriter.qml`

**Paths:**
```qml
readonly property string libraryScript: decodeURIComponent(
  Qt.resolvedUrl("song-library").toString().replace(/^file:\/\//, ""))
readonly property string libraryRuntimeDir: Quickshell.env("XDG_RUNTIME_DIR") + "/omarchy-songwriter"
readonly property string saveSelectionPath: libraryRuntimeDir + "/save-selection.json"
```

**State:**
```qml
property var librarySongs: []  // [{id,title,updatedAt}, ...] summaries for Open menu
property string libraryMenuKind: ""  // "" | "open"
```

**Mint id** (QML):
```javascript
function ensureSongId() {
  if (song && song.id) return song.id
  // uuidgen via Process once, or Math.random fallback is weak — prefer:
  // Crypto-less: use Date.now + random hex; or run `uuidgen` synchronously via helper on save.
}
```
Prefer: `song-library save` accepts staged JSON **without** id and mints UUID in bash (`uuidgen` / `/proc/sys/kernel/random/uuid`), then returns library; QML applies returned entry’s id back onto `song`.

**Save flow:**
1. Stop nothing required; keep playing OK.
2. Build payload `{ title: song.title, id: song.id || "", song: <plain song fields> }` — include full session fields needed to restore (bpm, keyIndex, sections, loop, octave, layout, instrument, laptopKeys, laptopOctave).
3. Write staging via existing `write-json.py` or FileView `setText`.
4. `Process` → `[libraryScript, "save"]`; on success parse stdout, set `librarySongs`, set `song.id`/`title` from saved entry, `statusText = "Saved"`, `persistSoon()`.

**Open flow:**
1. Ensure library loaded (`get` if empty).
2. Open menu on `menuOverlay` (same parenting pattern as SongStructure): list titles; clicking loads that entry’s `song` via `seedSong`, assigns `id`/`title`, `stopPlayback()`, `updateSong`/`song = …`, `persistSoon()`, `statusText = "Loaded …"`.
3. Optional trailing “Remove …” items or a second click affordance: include a delete action per row using a `delete` sub-action or long label `"Delete: Title"` at bottom — prefer each row is load, with a small separate delete list section `"Remove"` submenu **or** hold: simplest is Open menu items load, and each has companion — keep YAGNI: Open menu items load only; add `"Delete: <title>"` entries after a separator label disabled, OR one-shot: rightmost is enough — **implement delete as menu items prefixed with "Remove · "** under the load list.

**Load library on overlay open** (`open()`): fire `song-library get`.

**Transport bindings:**
```qml
songTitle: root.song.title || "Untitled"
onTitleEdited: root.applySongFields({ title: value }) // or updateSong merge
onSaveRequested: root.saveToLibrary()
onOpenRequested: root.openLibraryMenu()
```

**Step 1:** Implement helper Process + staging + menus.
**Step 2:** Manual checklist (when plugin linked): rename → Save → change chords → Open → pick → title/chords restore.
**Step 3:** Commit
```bash
git add Songwriter.qml
git commit -m "$(cat <<'EOF'
feat(song_library): wire save and open from transport

EOF
)"
```

---

### [x] Task 6: End-to-end verification + map check

**Status:** `done`
**Resume:** Complete — tests + maps verified
**Commits:** — (no map sync commit needed)

**Step 1:** `python3 tests/run.py` — all pass.
**Step 2:** `./bin/feature-map validate && ./bin/feature-map check`
**Step 3:** Confirm `song-library` is executable and referenced from QML.
**Step 4:** If maps drifted during Tasks 4–5, patch and commit
```bash
git add .features/*.yaml
git commit -m "$(cat <<'EOF'
docs(song_library): sync feature maps after wiring

EOF
)"
```
Only if there are map diffs.

---

### [x] Task 7: Final branch hygiene

**Status:** `done`
**Resume:** Complete
**Commits:** (plan commit pending)

**Step 1:** `git status` / `git log master..HEAD` — clean, commits on `feature/song-library` only.
**Step 2:** Do **not** merge to master or push unless user asks.
**Step 3:** Report worktree path + how to try: link worktree plugin or copy; library at `~/.local/share/songwriter/library.json`.

---

## Manual test plan

1. Open songwriter → title field shows Untitled (or restored title).
2. Edit title to “Demo”, place chords, Save → status Saved; file `~/.local/share/songwriter/library.json` contains entry.
3. Change chords, Open → choose Demo → previous chords restored; playback stopped if it was running.
4. Save again after edits → same `id`, updated `updatedAt`.
5. Remove via Open menu → entry gone; session song unchanged until next load.
6. Uninstall/reinstall mental model: deleting plugin files leaves `~/.local/share/songwriter/`.
