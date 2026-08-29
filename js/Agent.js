.pragma library

// Port of source SongJson (progressions + full song document).
// Prefer Model.js / Song.js globals when the test VM has already loaded them.

function wrapKey(index) {
  if (typeof wrap === "function")
    return wrap(index)
  var n = Number(index)
  if (!isFinite(n))
    return 0
  n = Math.round(n)
  var m = n % 12
  return m < 0 ? m + 12 : m
}

function wrapPc(pc) {
  if (typeof wrapPitchClass === "function")
    return wrapPitchClass(pc)
  var n = Number(pc)
  if (!isFinite(n))
    return 0
  n = Math.round(n)
  var m = n % 12
  return m < 0 ? m + 12 : m
}

function pcName(pc) {
  var names = typeof PC_NAMES !== "undefined"
    ? PC_NAMES
    : ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
  return names[wrapPc(pc)]
}

function nameOfChord(chord) {
  if (typeof chordName === "function")
    return chordName(chord.rootPc, chord.quality)
  var n = pcName(chord.rootPc)
  if (chord.quality === "minor")
    return n + "m"
  if (chord.quality === "diminished")
    return n + "dim"
  if (chord.quality === "augmented")
    return n + "aug"
  return n
}

function qualityOf(chord) {
  var q = chord && chord.quality
  if (q === "minor" || q === "diminished" || q === "augmented")
    return q
  return "major"
}

function numeralOf(chord, keyIndex) {
  if (typeof numeralFor === "function")
    return numeralFor(chord, keyIndex)
  return ""
}

function keyStation(index) {
  if (typeof station === "function")
    return station(index)
  var majors = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
  var minors = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "Bbm", "Fm", "Cm", "Gm", "Dm"]
  var i = wrapKey(index)
  return { major: majors[i], relativeMinor: minors[i] }
}

function rowsFor(measureCount) {
  if (typeof rowCount === "function")
    return rowCount(measureCount)
  if (measureCount <= 0)
    return 0
  return Math.floor((measureCount + 3) / 4)
}

function timeSigLabel(ts) {
  var n = ts && Number(ts.numerator)
  var d = ts && Number(ts.denominator)
  if (!isFinite(n) || n < 1)
    n = 4
  if (!isFinite(d) || d < 1)
    d = 4
  return n + "/" + d
}

function keyJson(keyIndex) {
  var idx = wrapKey(keyIndex)
  var s = keyStation(idx)
  return { index: idx, major: s.major, relativeMinor: s.relativeMinor }
}

function rowRepeatsJson(section) {
  var n = section && section.measures ? section.measures.length : 0
  var rows = rowsFor(n)
  var flags = section && section.rowRepeats ? section.rowRepeats : []
  var out = []
  for (var i = 0; i < rows; i++)
    out.push(i < flags.length && !!flags[i])
  return out
}

function chordObject(chord, keyIndex, loc) {
  var obj = {
    name: nameOfChord(chord),
    root: pcName(chord.rootPc),
    rootPc: wrapPc(chord.rootPc),
    quality: qualityOf(chord)
  }
  if (loc) {
    obj.bar = loc.bar
    obj.slot = loc.slot
  }
  var numeral = numeralOf(chord, keyIndex)
  if (numeral)
    obj.numeral = numeral
  return obj
}

function barProgressionText(measure) {
  var text = ""
  var slots = measure && measure.slots ? measure.slots : []
  for (var i = 0; i < slots.length; i++) {
    if (text)
      text += " "
    text += slots[i].chord ? nameOfChord(slots[i].chord) : "-"
  }
  return text
}

function sectionProgressionText(section) {
  var text = ""
  var measures = section && section.measures ? section.measures : []
  for (var i = 0; i < measures.length; i++) {
    if (i > 0)
      text += " | "
    text += barProgressionText(measures[i])
  }
  return text
}

function progressionsJson(song) {
  song = song || {}
  var keyIndex = song.keyIndex || 0
  var sections = song.sections || []
  var out = {
    key: keyJson(keyIndex),
    bpm: song.bpm,
    sections: []
  }
  for (var si = 0; si < sections.length; si++) {
    var section = sections[si]
    var chords = []
    var measures = section.measures || []
    for (var mi = 0; mi < measures.length; mi++) {
      var slots = measures[mi].slots || []
      for (var sl = 0; sl < slots.length; sl++) {
        if (!slots[sl].chord)
          continue
        chords.push(chordObject(slots[sl].chord, keyIndex, { bar: mi, slot: sl }))
      }
    }
    out.sections.push({
      name: section.name,
      timeSignature: timeSigLabel(section.timeSig),
      rowRepeats: rowRepeatsJson(section),
      progression: sectionProgressionText(section),
      chords: chords
    })
  }
  return out
}

function songJson(song) {
  song = song || {}
  var keyIndex = song.keyIndex || 0
  var sections = song.sections || []
  var out = {
    key: keyJson(keyIndex),
    bpm: song.bpm,
    sections: []
  }
  for (var si = 0; si < sections.length; si++) {
    var section = sections[si]
    var measures = []
    var srcMeasures = section.measures || []
    for (var mi = 0; mi < srcMeasures.length; mi++) {
      var slots = []
      var srcSlots = srcMeasures[mi].slots || []
      for (var sl = 0; sl < srcSlots.length; sl++) {
        slots.push(srcSlots[sl].chord
          ? chordObject(srcSlots[sl].chord, keyIndex, null)
          : null)
      }
      measures.push({ slots: slots })
    }
    out.sections.push({
      name: section.name,
      timeSignature: timeSigLabel(section.timeSig),
      rowRepeats: rowRepeatsJson(section),
      measures: measures
    })
  }
  return out
}
