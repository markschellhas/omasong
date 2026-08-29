.pragma library

// Port of source SongJson (progressions + full song document).
// Diatonic numerals are local: QML pragma libraries cannot see Model.js.

var AGENT_PC_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
var AGENT_NUMERALS = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
var AGENT_MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]
var AGENT_MAJOR_QUALITIES = ["major", "minor", "minor", "major", "major", "minor", "diminished"]
var AGENT_MAJOR_NAMES = ["C", "G", "D", "A", "E", "B", "F#", "Db", "Ab", "Eb", "Bb", "F"]
var AGENT_MINOR_NAMES = ["Am", "Em", "Bm", "F#m", "C#m", "G#m", "D#m", "Bbm", "Fm", "Cm", "Gm", "Dm"]

function agentWrapKey(index) {
  var n = Number(index)
  if (!isFinite(n))
    return 0
  n = Math.round(n)
  var m = n % 12
  return m < 0 ? m + 12 : m
}

function agentWrapPc(pc) {
  var n = Number(pc)
  if (!isFinite(n))
    return 0
  n = Math.round(n)
  var m = n % 12
  return m < 0 ? m + 12 : m
}

function pcName(pc) {
  return AGENT_PC_NAMES[agentWrapPc(pc)]
}

function nameOfChord(chord) {
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
  if (!chord)
    return ""
  var tonic = agentWrapPc(7 * agentWrapKey(keyIndex))
  var pc = agentWrapPc(chord.rootPc)
  var quality = qualityOf(chord)
  for (var i = 0; i < 7; i++) {
    if (agentWrapPc(tonic + AGENT_MAJOR_SCALE[i]) === pc && AGENT_MAJOR_QUALITIES[i] === quality)
      return AGENT_NUMERALS[i]
  }
  return ""
}

function keyStation(index) {
  var i = agentWrapKey(index)
  return { major: AGENT_MAJOR_NAMES[i], relativeMinor: AGENT_MINOR_NAMES[i] }
}

function rowsFor(measureCount) {
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

function bpmOf(song) {
  var n = Number(song && song.bpm)
  return isFinite(n) ? n : 120
}

function keyJson(keyIndex) {
  var idx = agentWrapKey(keyIndex)
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
    rootPc: agentWrapPc(chord.rootPc),
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
    bpm: bpmOf(song),
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
    bpm: bpmOf(song),
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
