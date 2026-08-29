.pragma library

// Port of source MusicTheory (circle stations, triads, payloads, meter).
// Polar / wedge helpers stay so CircleOfFifths.qml loads until Task 6.

var PC_NAMES = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

var QUALITY_NAMES = ["major", "minor", "diminished", "augmented"]

var NUMERALS = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]

var MAJOR_SCALE = [0, 2, 4, 5, 7, 9, 11]

var MAJOR_QUALITIES = ["major", "minor", "minor", "major", "major", "minor", "diminished"]

// Clockwise fifths from 12 o'clock: index 0 = C / Am.
var FIFTHS = [
  { major: "C", minor: "Am", accidentals: "0" },
  { major: "G", minor: "Em", accidentals: "1#" },
  { major: "D", minor: "Bm", accidentals: "2#" },
  { major: "A", minor: "F#m", accidentals: "3#" },
  { major: "E", minor: "C#m", accidentals: "4#" },
  { major: "B", minor: "G#m", accidentals: "5#" },
  { major: "F#", minor: "D#m", accidentals: "6#" },
  { major: "Db", minor: "Bbm", accidentals: "5b" },
  { major: "Ab", minor: "Fm", accidentals: "4b" },
  { major: "Eb", minor: "Cm", accidentals: "3b" },
  { major: "Bb", minor: "Gm", accidentals: "2b" },
  { major: "F", minor: "Dm", accidentals: "1b" }
]

var SECTORS = 12
var SECTOR_DEG = 360 / SECTORS
// PathAngleArc and screen-space cos/sin: 0° = 3 o'clock, clockwise.
var TOP_DEG = -90
// Pitch class of each major tonic, matching FIFTHS (C=0 … B=11).
var PITCH_CLASS = [0, 7, 2, 9, 4, 11, 6, 1, 8, 3, 10, 5]

function wrapPitchClass(pc) {
  var m = pc % 12
  return m < 0 ? m + 12 : m
}

function wrap(index) {
  var n = FIFTHS.length
  var m = index % n
  return m < 0 ? m + n : m
}

function tonicPc(index) {
  return wrapPitchClass(7 * wrap(index))
}

function station(index) {
  var k = FIFTHS[wrap(index)]
  return { major: k.major, relativeMinor: k.minor, accidentals: k.accidentals }
}

function keyAt(index) {
  return FIFTHS[wrap(index)]
}

function label(index) {
  var s = station(index)
  return s.major + " / " + s.relativeMinor
}

function qualityInt(quality) {
  var i = QUALITY_NAMES.indexOf(quality)
  return i
}

function qualityName(n) {
  var i = Number(n)
  if (i < 0 || i > 3 || !isFinite(i))
    return null
  return QUALITY_NAMES[i]
}

function triadIntervals(quality) {
  if (quality === "minor")
    return [3, 7]
  if (quality === "diminished")
    return [3, 6]
  if (quality === "augmented")
    return [4, 8]
  return [4, 7]
}

function chordName(rootPc, quality) {
  var n = PC_NAMES[wrapPitchClass(rootPc)]
  if (quality === "minor")
    return n + "m"
  if (quality === "diminished")
    return n + "dim"
  if (quality === "augmented")
    return n + "aug"
  return n
}

function encodeChord(chord) {
  var pc = wrapPitchClass(chord.rootPc)
  return "chord|" + chordName(pc, chord.quality) + "|" + pc + "|" + qualityInt(chord.quality)
}

function decodeChord(payload) {
  if (!payload || String(payload).indexOf("chord|") !== 0)
    return null
  var parts = String(payload).split("|")
  if (parts.length < 4)
    return null
  var pc = parseInt(parts[2], 10)
  var q = qualityName(parseInt(parts[3], 10))
  if (!isFinite(pc) || !q)
    return null
  return { rootPc: wrapPitchClass(pc), quality: q }
}

function diatonicTriads(keyIndex) {
  var tonic = tonicPc(keyIndex)
  var out = []
  for (var i = 0; i < 7; i++) {
    out.push({
      rootPc: wrapPitchClass(tonic + MAJOR_SCALE[i]),
      quality: MAJOR_QUALITIES[i]
    })
  }
  return out
}

function diatonic(index) {
  var t = diatonicTriads(index)
  return {
    I: chordName(t[0].rootPc, t[0].quality),
    ii: chordName(t[1].rootPc, t[1].quality),
    iii: chordName(t[2].rootPc, t[2].quality),
    IV: chordName(t[3].rootPc, t[3].quality),
    V: chordName(t[4].rootPc, t[4].quality),
    vi: chordName(t[5].rootPc, t[5].quality),
    vii: chordName(t[6].rootPc, t[6].quality)
  }
}

function numeralFor(chord, keyIndex) {
  var set = diatonicTriads(keyIndex)
  for (var i = 0; i < set.length; i++) {
    if (set[i].rootPc === chord.rootPc && set[i].quality === chord.quality)
      return NUMERALS[i]
  }
  return ""
}

function maxSlots(ts) {
  var n = ts && ts.numerator
  return n < 1 ? 1 : n
}

function beatsPerBar(ts) {
  if (!ts || ts.denominator <= 0)
    return 4
  return 4 * ts.numerator / ts.denominator
}

function triadMidi(chord, octave) {
  if (octave === undefined || octave === null)
    octave = 4
  var root = (octave + 1) * 12 + wrapPitchClass(chord.rootPc)
  var iv = triadIntervals(chord.quality)
  var n1 = root
  var n2 = root + iv[0]
  var n3 = root + iv[1]
  var kLow = 48
  var kHigh = 72
  while (n3 > kHigh && n1 - 12 >= kLow) {
    n1 -= 12
    n2 -= 12
    n3 -= 12
  }
  while (n1 < kLow) {
    n1 += 12
    n2 += 12
    n3 += 12
  }
  return [n1, n2, n3]
}

function subdominantIndex(tonic) {
  return wrap(tonic + 11)
}

function dominantIndex(tonic) {
  return wrap(tonic + 1)
}

function inKeyWedge(index, tonic) {
  var i = wrap(index)
  var t = wrap(tonic)
  return i === t || i === wrap(t + 1) || i === wrap(t + 11)
}

function wedgeChords(tonic) {
  var t = wrap(tonic)
  var sub = wrap(t + 11)
  var dom = wrap(t + 1)
  return [
    { index: t, ring: "major", roman: "I" },
    { index: sub, ring: "minor", roman: "ii" },
    { index: dom, ring: "minor", roman: "iii" },
    { index: sub, ring: "major", roman: "IV" },
    { index: dom, ring: "major", roman: "V" },
    { index: t, ring: "minor", roman: "vi" }
  ]
}

function wrapCursor(cursor, length) {
  var n = length > 0 ? length : 1
  var m = cursor % n
  return m < 0 ? m + n : m
}

function wedgeChordAt(tonic, cursor) {
  var list = wedgeChords(tonic)
  return list[wrapCursor(cursor, list.length)]
}

function wedgeChordByDegree(tonic, degree) {
  var list = wedgeChords(tonic)
  var n = Number(degree)
  if (!isFinite(n)) return null
  n = Math.floor(n)
  if (n < 1 || n > list.length) return null
  return list[n - 1]
}

function wedgeChordIndex(tonic, sector, ring) {
  var list = wedgeChords(tonic)
  var i = wrap(sector)
  for (var n = 0; n < list.length; n++) {
    if (list[n].index === i && list[n].ring === ring)
      return n
  }
  return -1
}

function wedgeStartDeg(tonic) {
  return sectorStartDeg(subdominantIndex(tonic))
}

function wedgeSweepDeg() {
  return SECTOR_DEG * 3
}

function sectorMidDeg(index) {
  return wrap(index) * SECTOR_DEG + TOP_DEG
}

function sectorStartDeg(index) {
  return sectorMidDeg(index) - SECTOR_DEG / 2
}

function sectorSweepDeg() {
  return SECTOR_DEG
}

function sectorEdgeDeg(index) {
  return sectorStartDeg(index)
}

function degToRad(deg) {
  return deg * Math.PI / 180
}

function polarX(cx, radius, deg) {
  return cx + radius * Math.cos(degToRad(deg))
}

function polarY(cy, radius, deg) {
  return cy + radius * Math.sin(degToRad(deg))
}

function radialSvg(cx, cy, rInner, rOuter) {
  var parts = []
  for (var i = 0; i < SECTORS; i++) {
    var deg = sectorEdgeDeg(i)
    parts.push(
      "M " + polarX(cx, rInner, deg).toFixed(2) + " " + polarY(cy, rInner, deg).toFixed(2)
      + " L " + polarX(cx, rOuter, deg).toFixed(2) + " " + polarY(cy, rOuter, deg).toFixed(2)
    )
  }
  return parts.join(" ")
}

function midiToHz(midi) {
  return 440 * Math.pow(2, (midi - 69) / 12)
}

function triad(index, ring) {
  var minor = ring === "minor"
  var quality = minor ? "minor" : "major"
  var pc = minor ? wrapPitchClass(tonicPc(index) + 9) : tonicPc(index)
  var notes = triadMidi({ rootPc: pc, quality: quality })
  var s = station(index)
  return {
    root: midiToHz(notes[0]),
    third: midiToHz(notes[1]),
    fifth: midiToHz(notes[2]),
    notes: notes,
    label: minor ? s.relativeMinor : s.major,
    minor: minor
  }
}

function hitTest(x, y, cx, cy, minorInner, minorOuter, majorInner, majorOuter) {
  var dx = x - cx
  var dy = y - cy
  var r = Math.sqrt(dx * dx + dy * dy)
  var ring = ""
  if (r >= minorInner && r <= minorOuter)
    ring = "minor"
  else if (r >= majorInner && r <= majorOuter)
    ring = "major"
  if (!ring)
    return null

  var fromTop = Math.atan2(dy, dx) * 180 / Math.PI - TOP_DEG
  fromTop = ((fromTop % 360) + 360) % 360
  return { index: Math.round(fromTop / SECTOR_DEG) % SECTORS, ring: ring }
}
