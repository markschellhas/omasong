# Agent instructions

Any agent that can run a command can read the chords that have been added to the current song:

```bash
python3 ./chords-agent progressions
```

That is the contract. Do not infer the song from source defaults or the starter Verse/Chorus.

| Command | Output |
|---------|--------|
| `python3 ./chords-agent progressions` | Placed chords, grouped by section, plus a `C \| G F C \| Dm` string |
| `python3 ./chords-agent song` | Full document; empty slots are `null` |
| `python3 ./chords-agent health` | Live app is up (exit `0`) or not (exit `2`) |

`--live` skips the on-disk snapshot and fails if the app is not running (exit `2`).

`chords-agent` talks to the overlay on `127.0.0.1` (port `17891`, or `$CHORDS_AGENT_PORT`, or the port in `agent-api.json`). If the process is down it prints the last snapshot from `$CHORDS_AGENT_HOME` or `~/.config/chords-and-tabs/`.

## Example `progressions` body

```json
{
  "key": { "index": 0, "major": "C", "relativeMinor": "Am" },
  "bpm": 120,
  "sections": [
    {
      "name": "Verse",
      "timeSignature": "4/4",
      "rowRepeats": [false],
      "progression": "C | G F C | Dm",
      "chords": [
        { "name": "C", "root": "C", "rootPc": 0, "quality": "major", "bar": 0, "slot": 0, "numeral": "I" }
      ]
    }
  ]
}
```

Empty slots are omitted from `chords` and shown as `-` in `progression`. Roman numerals are included when the chord is diatonic in the circle’s current key.

<!-- feature-map:start -->
## Feature Map

**ALWAYS** use Feature Map before feature work, debugging, PRDs, or plans.
Do not implement from a cold grep when a map exists.

```bash
./bin/feature-map list
./bin/feature-map search <keyword>
./bin/feature-map find <path-fragment>
./bin/feature-map <feature-name>
```

Maps in `.features/*.yaml` are the authoritative cross-app architecture source.
Keep them dense: fields, not essays.

If `list` is empty or search/find miss the area you are about to change,
**scour the existing code and author maps first** (skill:
`feature-map` → `references/existing-repos.md`). Cluster by user-visible
capability, not by file. Prefer `entry_points` that exist on disk, then
run `feature-map validate` and `feature-map check`.
<!-- feature-map:end -->
