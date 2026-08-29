# Songwriter for Omarchy

Chords & Tabs as an Omarchy overlay: pick a key on the circle of fifths, write
verse/chorus slots, play them back, and use a two-octave piano.

Plugin id: `io.github.markschellhas.songwriter`

This is a port of the Chords & Tabs songwriter (transport, circle of fifths,
song structure, and keyboard) into a third-party Omarchy shell plugin.

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

## Usage

- **Transport** — Play walks filled chord slots at the current BPM. Stop ends
  playback. Loop repeats the song. Tap tempo from a few taps.
- **Circle of fifths** — Click a major or minor wedge to set the key. Changing
  key transposes the written chords. Tone mode (`T`, or the Tone button) plays
  I–vi without changing key; keys `1`–`6` jump to those degrees.
- **Song structure** — Verse and chorus rows of chord cells. Click a cell to
  type a symbol (`C`, `Am`, `F#dim7`, `G/B`). Right-click or double-click
  previews. Add or remove sections as needed.
- **Keyboard** — Two octaves from the current base. Computer keys match the
  original app (`a s d f g h j k l ; '` white, `w e r t y u i o p [` black).
  Space is sustain. Octave buttons shift the range.

Sound is a sine-wave placeholder via `play-notes.py` (`pw-play`, `paplay`, or
`aplay`). The current song is saved to
`~/.local/state/omarchy/songwriter/song.json`.

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

The original Svelte MIDI studio remains under `frontend/` as the feature
reference for this port.

## License

MIT
