# Songwriter for Omarchy

Omarchy shell plugin that ports **[Chords & Tabs](https://github.com/markschellhas/chords-and-tabs)** — the JUCE song-builder — into a bar chip and overlay.

Source product (read-only, do not modify): https://github.com/markschellhas/chords-and-tabs

Plugin id: `io.github.markschellhas.songwriter`

Product contract: [PRD.md](PRD.md) — exactly the twelve features in the source `.features/` directory. Port sequencing: [MIGRATION_PLAN.md](MIGRATION_PLAN.md).

## Features (from the source maps)

| Feature | What it does |
|---------|----------------|
| `circle_of_fifths` | Rotate so the active key sits at 12 o'clock; drag wedges or I–vii° chips into bars |
| `music_theory` | Triads, diatonic sets, meters, `chord\|name\|rootPc\|quality` payloads |
| `song_structure` | Verse/Chorus (and extra) sections; bar count follows 4/4, 3/4, 2/4, 6/8 |
| `chord_slots` | Place, split (drop on a filled chord), edge-resize, clear |
| `row_repeats` | `:||` at the end of each 4-bar row plays that row twice |
| `playback` | Play / Stop / Loop / BPM 40–240 / Space; playhead and sounding-note highlight |
| `piano_keyboard` | C3–C5; click keys; light triads from play, preview, or selection |
| `instruments` | Piano, Electric Piano, Organ, Pad, Strings |
| `laptop_keys` | Off by default; A=C, W=C♯, …; Z/X octave; steals H/J/K/L when on |
| `region_focus` | j/k cycle Circle / Song / Keyboard; h/l rotate key or cycle sound |
| `agent_api` | `chords-agent progressions \| song \| health` on 127.0.0.1:17891 |
| `audio_device` | PipeWire output in this plugin (no JUCE Device dialog) |

Changing the circle does **not** transpose placed chords. Chords are triads, not typed symbols.

## Install

```bash
omarchy plugin add https://github.com/markschellhas/songwriter.git --enable
omarchy bar move io.github.markschellhas.songwriter --section right
```

Left-click the bar chip to open the overlay. Clicks outside the card pass
through to the desktop. Esc closes.

### Keyboard shortcut

Omarchy does not load Hyprland binds from plugins, so add this to
`~/.config/hypr/bindings.lua` after install.

```lua
o.bind("SUPER + CTRL + ALT + S", "Songwriter", "omarchy-shell shell toggle io.github.markschellhas.songwriter")
```

## Status

The overlay chrome is in place. Behavior is **not** yet at parity with the PRD (drag-to-slot, rotating circle, row repeats, agent CLI, and the source laptop-key map are still to do). Until the migration plan is done, treat this as a port in progress.

## Remove

```bash
omarchy plugin remove io.github.markschellhas.songwriter
```

## Develop locally

```bash
omarchy plugin validate ~/.config/omarchy/plugins/io.github.markschellhas.songwriter
python3 tests/run.py
omarchy-shell shell rescanPlugins
```

`frontend/` is a leftover Svelte MIDI studio. It is not the source product. See the banner in `frontend/specification.md`.

## License

Follow the source product’s GPLv3-style terms when this port is complete. JUCE itself is licensed separately and is not vendored here.
