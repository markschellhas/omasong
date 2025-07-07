# Audio to MIDI Conversion Guide

A comprehensive guide to converting vocal tracks to MIDI files with optimal musical results.

## 🎯 Overview

The `vocal_to_midi.py` script converts vocal audio tracks into MIDI melody files using advanced pitch detection and musical processing. This guide covers how to fine-tune the parameters for different musical styles and use cases.

## 📋 Quick Reference

### Basic Usage
```bash
# Default settings (recommended for most vocals)
python vocal_to_midi.py vocal_track.wav

# Custom output file
python vocal_to_midi.py vocal_track.wav -o melody.mid
```

### Key Parameters
| Parameter | Default | Description | Effect |
|-----------|---------|-------------|---------|
| `--min-duration` | 0.3s | Minimum note length | Higher = fewer, longer notes |
| `--pitch-threshold` | 1.0 | Semitone change sensitivity | Higher = less sensitive, fewer notes |
| `--velocity` | 80 | MIDI note velocity | 0-127, affects volume |
| `--quantize` | False | Snap to musical beats | True = rhythmically aligned |
| `--light-smoothing` | False | Reduce pitch smoothing | True = more detail, potentially noisier |

## 🎼 Musical Style Presets

### 1. Pop/Rock Vocals (Recommended Default)
```bash
python vocal_to_midi.py vocal.wav --min-duration 0.3 --pitch-threshold 1.0
```
**Best for:** Most modern vocals, clear melodies
**Result:** Clean, musical notes with natural phrasing

### 2. Ballads & Slow Songs
```bash
python vocal_to_midi.py vocal.wav --min-duration 0.5 --pitch-threshold 1.5 --quantize
```
**Best for:** Slow, expressive vocals with sustained notes
**Result:** Longer, more sustained notes with rhythmic alignment

### 3. R&B/Jazz with Runs
```bash
python vocal_to_midi.py vocal.wav --min-duration 0.2 --pitch-threshold 0.5 --light-smoothing
```
**Best for:** Vocals with melisma, runs, and embellishments
**Result:** More detailed note transitions, captures vocal runs

### 4. Rap/Spoken Word
```bash
python vocal_to_midi.py vocal.wav --min-duration 0.1 --pitch-threshold 2.0 --quantize
```
**Best for:** Rap verses, spoken word with pitch variation
**Result:** Captures pitch patterns while filtering speech noise

### 5. Classical/Opera
```bash
python vocal_to_midi.py vocal.wav --min-duration 0.4 --pitch-threshold 1.0 --velocity 100
```
**Best for:** Operatic vocals, classical singing
**Result:** Strong, sustained notes with proper dynamics

## 🔧 Parameter Deep Dive

### Minimum Duration (`--min-duration`)
Controls the shortest allowable note length.

**Examples:**
```bash
# Very short notes (detailed but potentially noisy)
python vocal_to_midi.py vocal.wav --min-duration 0.1

# Medium notes (balanced)
python vocal_to_midi.py vocal.wav --min-duration 0.3

# Long notes only (clean but might miss quick passages)
python vocal_to_midi.py vocal.wav --min-duration 0.6
```

**Guidelines:**
- **0.1-0.2s**: Fast vocals, rap, detailed melismatic runs
- **0.3-0.4s**: Most vocals, balanced approach
- **0.5-0.8s**: Ballads, sustained singing, very clean output

### Pitch Threshold (`--pitch-threshold`)
Determines how much pitch must change to trigger a new note.

**Examples:**
```bash
# Very sensitive (captures every pitch change)
python vocal_to_midi.py vocal.wav --pitch-threshold 0.25

# Balanced (ignores vibrato, captures real notes)
python vocal_to_midi.py vocal.wav --pitch-threshold 1.0

# Less sensitive (only major pitch changes)
python vocal_to_midi.py vocal.wav --pitch-threshold 2.0
```

**Guidelines:**
- **0.25-0.5**: Detailed vocal runs, melisma, jazz
- **1.0-1.5**: Most vocals, filters vibrato
- **2.0-3.0**: Simple melodies, reduces noise

### Smoothing (`--light-smoothing`)
Controls how aggressively pitch is smoothed.

```bash
# Aggressive smoothing (default) - cleaner but less detail
python vocal_to_midi.py vocal.wav

# Light smoothing - more detail but potentially noisier
python vocal_to_midi.py vocal.wav --light-smoothing
```

**Use aggressive smoothing for:**
- Pop vocals
- Recordings with background noise
- Vibrato-heavy singing
- Clean, simple melodies

**Use light smoothing for:**
- Jazz vocals with subtle inflections
- Beatboxing or vocal percussion
- Very clean, isolated vocals
- When you need maximum detail

### Timing Quantization (`--quantize`)
Snaps note timing to musical beats (assumes 120 BPM).

```bash
# Free timing (follows natural vocal rhythm)
python vocal_to_midi.py vocal.wav

# Quantized timing (snaps to beat grid)
python vocal_to_midi.py vocal.wav --quantize
```

**Use quantization for:**
- Rhythmic vocals that should align to beats
- Creating backing tracks
- When tempo consistency is important
- Dance/electronic music vocals

**Avoid quantization for:**
- Expressive ballads
- Jazz vocals with rubato
- Free-form or improvisational vocals
- When natural timing is important

## 📊 Results Analysis

### Understanding the Statistics

When the script completes, it shows:

```
📊 Statistics:
   Total duration: 182.90 seconds
   Number of notes: 123
   Note coverage: 80.2%
   Note range: F#2 to G#6
```

**What these mean:**
- **Number of notes**: Lower = cleaner, higher = more detailed
- **Note coverage**: Percentage of time with detected notes
- **Note range**: Vocal range in the recording

### Optimization Guidelines

**Too many notes (>200 for a 3-minute song)?**
- Increase `--pitch-threshold` to 1.5 or 2.0
- Increase `--min-duration` to 0.4 or 0.5
- Use default (aggressive) smoothing

**Too few notes (<50 for a 3-minute song)?**
- Decrease `--pitch-threshold` to 0.5
- Decrease `--min-duration` to 0.2
- Use `--light-smoothing`

**Notes sound choppy/robotic?**
- Increase `--min-duration`
- Increase `--pitch-threshold`
- Ensure aggressive smoothing (default)

**Missing vocal details/runs?**
- Use `--light-smoothing`
- Decrease `--pitch-threshold` to 0.5
- Decrease `--min-duration` to 0.2

## 🎯 Common Use Cases

### 1. Create Karaoke Melody Guide
```bash
python vocal_to_midi.py original_vocal.wav -o karaoke_guide.mid --min-duration 0.4 --quantize
```

### 2. Analyze Vocal Technique
```bash
python vocal_to_midi.py vocal.wav --light-smoothing --min-duration 0.1 --preview
```

### 3. Create Backing Harmony
```bash
python vocal_to_midi.py lead_vocal.wav -o harmony_guide.mid --min-duration 0.3 --pitch-threshold 1.5
```

### 4. Study Melodic Patterns
```bash
python vocal_to_midi.py vocal.wav --preview --min-duration 0.2
```

### 5. Extract Main Melody Only
```bash
python vocal_to_midi.py vocal.wav --min-duration 0.5 --pitch-threshold 2.0 --velocity 100
```

## 🔍 Visual Analysis

Use the `--preview` flag to see pitch detection in action:

```bash
python vocal_to_midi.py vocal.wav --preview
```

This shows:
- **Raw pitch track**: Noisy pitch detection
- **Smoothed pitch**: Cleaned up version
- **MIDI notes**: Final discrete notes

**Reading the preview:**
- Horizontal lines = sustained notes
- Gaps = silence or undetected pitch
- Smooth curves = good detection
- Jagged lines = may need more smoothing

## ⚡ Performance Tips

### For Best Results:
1. **Use isolated vocal tracks** (output from audio splitter)
2. **Normalize audio levels** before processing
3. **Remove background noise** if possible
4. **Process shorter segments** for very long files

### File Preparation:
```bash
# First, extract vocals using the audio splitter
python audio_splitter.py song.mp3

# Then convert the vocal stem
python vocal_to_midi.py output/song_vocals.wav
```

## 🚨 Troubleshooting

### "No notes detected"
**Causes:**
- Input file has no vocals
- Audio level too low
- Too much background noise

**Solutions:**
```bash
# Try more sensitive settings
python vocal_to_midi.py vocal.wav --pitch-threshold 0.5 --min-duration 0.1 --light-smoothing

# Check with preview
python vocal_to_midi.py vocal.wav --preview
```

### "Too many notes"
**Solutions:**
```bash
# Use cleaner settings
python vocal_to_midi.py vocal.wav --pitch-threshold 2.0 --min-duration 0.5

# Or very clean preset
python vocal_to_midi.py vocal.wav --min-duration 0.6 --pitch-threshold 1.5
```

### "Notes are wrong pitch"
**Causes:**
- Pitch detection algorithm limitations
- Harmonies interfering with melody
- Background instruments bleeding through

**Solutions:**
- Use cleaner vocal source
- Try different smoothing settings
- Check input with `--preview`

### "Timing is off"
**Solutions:**
```bash
# For rhythmic alignment
python vocal_to_midi.py vocal.wav --quantize

# For natural timing
python vocal_to_midi.py vocal.wav  # (no quantize)
```

## 📝 Example Workflows

### Workflow 1: Complete Song Analysis
```bash
# 1. Split the song
python audio_splitter.py full_song.mp3 -o stems/

# 2. Convert vocals to MIDI
python vocal_to_midi.py stems/full_song_vocals.wav -o melody.mid

# 3. Fine-tune if needed
python vocal_to_midi.py stems/full_song_vocals.wav -o melody_clean.mid --min-duration 0.4 --pitch-threshold 1.5
```

### Workflow 2: Detailed Vocal Study
```bash
# Extract with maximum detail
python vocal_to_midi.py vocal.wav -o detailed.mid --light-smoothing --min-duration 0.1 --pitch-threshold 0.5 --preview

# Create clean version for playback
python vocal_to_midi.py vocal.wav -o clean.mid --min-duration 0.4 --pitch-threshold 1.5
```

### Workflow 3: Rhythm Track Creation
```bash
# Quantized melody for backing tracks
python vocal_to_midi.py vocal.wav -o backing.mid --quantize --min-duration 0.3 --velocity 90
```

## 🎵 Integration with DAWs

The generated MIDI files work with:
- **Logic Pro**: Drag and drop into track
- **Ableton Live**: Import to MIDI track
- **FL Studio**: Load into Piano Roll
- **Pro Tools**: Import MIDI file
- **Reaper**: Insert as new MIDI item
- **GarageBand**: Drag to software instrument track

### DAW-Specific Tips:
- **Transpose** if needed (vocal recordings may be in different keys)
- **Adjust velocity** for desired volume
- **Quantize further** in DAW if needed
- **Use appropriate instrument** (voice, lead synth, etc.)

---

*For more information, see the main README.md or run `python vocal_to_midi.py --help`* 