# Mark's Songwriter Board

Omarchy shell plugin: a bar chip and overlay for circle of fifths, song structure, piano, and guitar tab.

Plugin id: `markschellhas.songwriter`

## Features

| Feature | What it does |
|---------|----------------|
| `circle_of_fifths` | Rotate so the active key sits at 12 o'clock; drag wedges or I–vii° chips into bars |
| `music_theory` | Triads, diatonic sets, `chord\|name\|rootPc\|quality` payloads |
| `song_structure` | Verse/Chorus (and extra) sections; four 4/4 bars by default, add or trim rows of four |
| `chord_slots` | Place, split (drop on a filled chord), edge-resize, clear |
| `row_repeats` | `:||` at the end of each 4-bar row plays that row twice |
| `playback` | Play / Stop / Loop / BPM 40–240 / Space; playhead and sounding-note highlight |
| `piano_keyboard` | C3–C5; click keys; light triads from play, preview, or selection |
| `instruments` | Piano, Electric Piano, Organ, Pad, Strings |
| `laptop_keys` | Off by default; A=C, W=C♯, …; Z/X octave; steals H/J/K/L when on |
| `region_focus` | j/k or ↑/↓ cycle Circle / Song / Keyboard; h/l or ←/→ act on the highlighted region; Tab moves Song cells |
| `agent_api` | `chords-agent progressions \| song \| health` on 127.0.0.1:17891 |
| `audio_device` | PipeWire output |

Changing the circle does **not** transpose placed chords. Chords are triads, not typed symbols.

## Install

```bash
omarchy plugin add https://github.com/markschellhas/songwriter.git --enable
omarchy bar move markschellhas.songwriter --section right
```

Left-click the bar chip to open the overlay. Clicks outside the card pass
through to the desktop. Esc closes.

### Keyboard shortcut

Omarchy does not load Hyprland binds from plugins, so add this to
`~/.config/hypr/bindings.lua` after install.

```lua
o.bind("SUPER + CTRL + ALT + S", "Songwriter", "omarchy-shell shell toggle markschellhas.songwriter")
```

## Status

The overlay’s capabilities are mapped in `.features/` (circle, slots, timeline, piano, guitar tab, laptop keys, region focus, `chords-agent`).

Automated check: `python3 tests/run.py`. Full overlay and `omarchy plugin validate` need an Omarchy host.

## Remove

```bash
omarchy plugin remove markschellhas.songwriter
```

## Develop locally

```bash
omarchy plugin validate ~/.config/omarchy/plugins/markschellhas.songwriter
python3 tests/run.py
omarchy-shell shell rescanPlugins
```

## License

Code is MIT. See [LICENSE](LICENSE).

Piano samples in `samples/piano/` are [Salamander Grand Piano](https://archive.org/details/SalamanderGrandPianoV3) by Alexander Holm, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). See `samples/piano/ATTRIBUTION.txt`.
