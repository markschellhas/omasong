.pragma library

// Parallel-mode colour grid: fixed root, seven modes, seven degrees.

var LETTERS = ["C", "D", "E", "F", "G", "A", "B"]

var NATURAL_PC = [0, 2, 4, 5, 7, 9, 11]

var MODE_NAMES = ["Lydian", "Ionian", "Mixolydian", "Dorian", "Aeolian", "Phrygian", "Locrian"]

var MODE_ABBREV = ["Lyd", "Ion", "Mix", "Dor", "Aeo", "Phr", "Loc"]

// Brightness order; each step down flattens degrees 4, 7, 3, 6, 2, 5.
var MODE_INTERVALS = [
  [0, 2, 4, 6, 7, 9, 11],
  [0, 2, 4, 5, 7, 9, 11],
  [0, 2, 4, 5, 7, 9, 10],
  [0, 2, 3, 5, 7, 9, 10],
  [0, 2, 3, 5, 7, 8, 10],
  [0, 1, 3, 5, 7, 8, 10],
  [0, 1, 3, 5, 6, 8, 10]
]

var FLATTEN_SEQUENCE = [4, 7, 3, 6, 2, 5]

var COMMON_MODE_INDICES = [1, 2, 3, 4]

var ROOT_SPELLINGS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

function wrapPc(pc) {
  var m = pc % 12
  return m < 0 ? m + 12 : m
}

function letterIndex(name) {
  if (!name || !name.length)
    return 0
  return LETTERS.indexOf(name.charAt(0).toUpperCase())
}

function parseNotePc(name) {
  var li = letterIndex(name)
  if (li < 0)
    return 0
  var alter = 0
  for (var i = 1; i < name.length; i++) {
    if (name.charAt(i) === "#")
      alter++
    else if (name.charAt(i) === "b")
      alter--
  }
  return wrapPc(NATURAL_PC[li] + alter)
}

function formatNote(pc, letterIdx) {
  var li = ((letterIdx % 7) + 7) % 7
  var natural = NATURAL_PC[li]
  var alter = pc - natural
  while (alter > 6)
    alter -= 12
  while (alter < -6)
    alter += 12
  var letter = LETTERS[li]
  if (alter === 0)
    return letter
  if (alter === 1)
    return letter + "#"
  if (alter === -1)
    return letter + "b"
  if (alter === 2)
    return letter + "##"
  if (alter === -2)
    return letter + "bb"
  return letter + (alter > 0 ? "#" : "b")
}

function rootName(rootPc) {
  return ROOT_SPELLINGS[wrapPc(rootPc)]
}

function scaleNotes(rootPc, modeIndex) {
  var intervals = MODE_INTERVALS[modeIndex]
  var rn = rootName(rootPc)
  var rli = letterIndex(rn)
  var out = []
  for (var d = 0; d < 7; d++) {
    var pc = wrapPc(rootPc + intervals[d])
    var name = formatNote(pc, rli + d)
    out.push({ degree: d, pc: pc, name: name })
  }
  return out
}

function intervalPc(a, b) {
  return wrapPc(b - a)
}

function triadQuality(rootPc, thirdPc, fifthPc) {
  var i3 = intervalPc(rootPc, thirdPc)
  var i5 = intervalPc(rootPc, fifthPc)
  if (i3 === 3 && i5 === 6)
    return "diminished"
  if (i3 === 3 && i5 === 7)
    return "minor"
  if (i3 === 4 && i5 === 7)
    return "major"
  if (i3 === 4 && i5 === 8)
    return "augmented"
  return "major"
}

function seventhKind(rootPc, seventhPc, triadQ) {
  var i7 = intervalPc(rootPc, seventhPc)
  if (triadQ === "diminished") {
    if (i7 === 9)
      return "dim7"
    if (i7 === 10)
      return "half-dim7"
    return "dim7"
  }
  if (triadQ === "minor") {
    if (i7 === 10)
      return "min7"
    if (i7 === 11)
      return "min-maj7"
    return "min7"
  }
  if (triadQ === "major" || triadQ === "augmented") {
    if (i7 === 10)
      return "dom7"
    if (i7 === 11)
      return "maj7"
    return "maj7"
  }
  return "maj7"
}

function chordSymbol(rootNameStr, triadQ, seventhKindName) {
  var sym = rootNameStr
  if (triadQ === "minor")
    sym += "m"
  else if (triadQ === "diminished")
    sym += "dim"
  else if (triadQ === "augmented")
    sym += "aug"
  if (!seventhKindName)
    return sym
  if (seventhKindName === "maj7")
    return triadQ === "major" || triadQ === "augmented" ? sym + "maj7" : sym + "maj7"
  if (seventhKindName === "dom7")
    return sym + "7"
  if (seventhKindName === "min7")
    return sym + "7"
  if (seventhKindName === "min-maj7")
    return sym + "(maj7)"
  if (seventhKindName === "half-dim7")
    return sym + "7b5"
  if (seventhKindName === "dim7")
    return sym + "7"
  return sym
}

function cellChord(rootPc, modeIndex, degreeIndex, useSevenths) {
  var scale = scaleNotes(rootPc, modeIndex)
  var d = degreeIndex % 7
  var root = scale[d]
  var third = scale[(d + 2) % 7]
  var fifth = scale[(d + 4) % 7]
  var triadQ = triadQuality(root.pc, third.pc, fifth.pc)
  var seventh = scale[(d + 6) % 7]
  var s7 = useSevenths ? seventhKind(root.pc, seventh.pc, triadQ) : ""
  var symbol = chordSymbol(root.name, triadQ, s7)
  var pitches = [root.pc, third.pc, fifth.pc]
  if (useSevenths)
    pitches.push(seventh.pc)
  return {
    rootPc: root.pc,
    rootName: root.name,
    quality: triadQ,
    seventh: s7,
    symbol: symbol,
    pitches: pitches,
    modeIndex: modeIndex,
    degreeIndex: d,
    unstableTonic: modeIndex === 6 && d === 0 && triadQ === "diminished"
  }
}

function chordKey(chord) {
  if (!chord)
    return ""
  return wrapPc(chord.rootPc) + ":" + chord.quality + ":" + (chord.seventh || "")
}

function chordsEqual(a, b) {
  return chordKey(a) === chordKey(b)
}

function homeScale(rootPc, homeModeIndex) {
  return scaleNotes(rootPc, homeModeIndex)
}

function romanNumeral(chord, rootPc, homeModeIndex) {
  if (!chord)
    return ""
  var home = homeScale(rootPc, homeModeIndex)
  var degree = -1
  var alter = 0
  var chordLetter = letterIndex(chord.rootName || "")
  var i
  for (i = 0; i < 7; i++) {
    if (letterIndex(home[i].name) !== chordLetter)
      continue
    degree = i
    var diff = wrapPc(wrapPc(chord.rootPc) - home[i].pc)
    if (diff === 0)
      alter = 0
    else if (diff === 1)
      alter = 1
    else if (diff === 11)
      alter = -1
    else
      degree = -1
    break
  }
  if (degree < 0)
    return ""
  var numerals = ["I", "II", "III", "IV", "V", "VI", "VII"]
  var base = numerals[degree]
  var prefix = ""
  if (alter === -1)
    prefix = "♭"
  else if (alter === 1)
    prefix = "♯"
  var body
  if (chord.quality === "diminished")
    body = base.toLowerCase() + "°"
  else if (chord.quality === "augmented")
    body = base.toLowerCase() + "+"
  else if (chord.quality === "minor")
    body = base.toLowerCase()
  else
    body = base
  return prefix + body
}

function isDiatonicToHome(chord, rootPc, homeModeIndex, useSevenths) {
  if (!chord)
    return false
  for (var d = 0; d < 7; d++) {
    var c = cellChord(rootPc, homeModeIndex, d, useSevenths)
    if (chordsEqual(c, chord))
      return true
  }
  return false
}

function sharedToneCount(chordA, chordB) {
  if (!chordA || !chordB)
    return 0
  var set = {}
  var i
  for (i = 0; i < chordA.pitches.length; i++)
    set[chordA.pitches[i]] = true
  var n = 0
  for (i = 0; i < chordB.pitches.length; i++) {
    if (set[chordB.pitches[i]])
      n++
  }
  return n
}

function rowChangedDegrees(modeRow) {
  if (modeRow <= 0 || modeRow >= MODE_NAMES.length)
    return []
  return [FLATTEN_SEQUENCE[modeRow - 1] - 1]
}

function cellChangedFromAbove(modeIndex, degreeIndex, rootPc, useSevenths, prevModeIndex) {
  if (prevModeIndex < 0)
    return false
  var above = cellChord(rootPc, prevModeIndex, degreeIndex, useSevenths)
  var here = cellChord(rootPc, modeIndex, degreeIndex, useSevenths)
  return !chordsEqual(above, here)
}

function visibleModeIndices(showAll) {
  return showAll ? [0, 1, 2, 3, 4, 5, 6] : COMMON_MODE_INDICES.slice()
}

function visibleModeCount(showAll) {
  return showAll ? 7 : COMMON_MODE_INDICES.length
}

function visibleModeIndex(rowIndex, showAll) {
  var ids = visibleModeIndices(showAll)
  if (rowIndex < 0 || rowIndex >= ids.length)
    return -1
  return ids[rowIndex]
}

function modeName(modeIndex) {
  return MODE_NAMES[modeIndex] || ""
}

function modeAbbrev(modeIndex) {
  return MODE_ABBREV[modeIndex] || ""
}

function cellInfo(rootPc, modeIndex, degreeIndex, homeModeIndex, useSevenths, prevModeIndex) {
  var chord = cellChord(rootPc, modeIndex, degreeIndex, useSevenths)
  return {
    modeIndex: modeIndex,
    degreeIndex: degreeIndex,
    symbol: chord.symbol,
    numeral: romanNumeral(chord, rootPc, homeModeIndex),
    diatonic: isDiatonicToHome(chord, rootPc, homeModeIndex, useSevenths),
    changedFromAbove: cellChangedFromAbove(modeIndex, degreeIndex, rootPc, useSevenths, prevModeIndex),
    unstableTonic: !!chord.unstableTonic,
    quality: chord.quality,
    rootPc: chord.rootPc,
    seventh: chord.seventh
  }
}

function buildGrid(rootPc, homeModeIndex, useSevenths, showAllModes) {
  var rows = []
  var modeIndices = showAllModes ? [0, 1, 2, 3, 4, 5, 6] : COMMON_MODE_INDICES
  var r
  for (r = 0; r < modeIndices.length; r++) {
    var mi = modeIndices[r]
    var prevMi = r > 0 ? modeIndices[r - 1] : -1
    var cells = []
    var d
    for (d = 0; d < 7; d++) {
      var chord = cellChord(rootPc, mi, d, useSevenths)
      cells.push({
        modeIndex: mi,
        degreeIndex: d,
        chord: chord,
        numeral: romanNumeral(chord, rootPc, homeModeIndex),
        diatonic: isDiatonicToHome(chord, rootPc, homeModeIndex, useSevenths),
        changedFromAbove: cellChangedFromAbove(mi, d, rootPc, useSevenths, prevMi)
      })
    }
    rows.push({
      modeIndex: mi,
      modeName: MODE_NAMES[mi],
      distanceFromHome: Math.abs(mi - homeModeIndex),
      cells: cells
    })
  }
  return rows
}

function duplicateCells(grid, modeIndex, degreeIndex, useSevenths, rootPc) {
  var target = cellChord(rootPc, modeIndex, degreeIndex, useSevenths)
  var key = chordKey(target)
  var hits = []
  var r, c
  for (r = 0; r < grid.length; r++) {
    for (c = 0; c < grid[r].cells.length; c++) {
      var cell = grid[r].cells[c]
      if (chordKey(cell.chord) === key)
        hits.push({ modeIndex: cell.modeIndex, degreeIndex: cell.degreeIndex })
    }
  }
  return hits
}

function chordMidiNotes(chord, octave) {
  if (octave === undefined || octave === null)
    octave = 4
  var base = (octave + 1) * 12
  var out = []
  var i
  for (i = 0; i < chord.pitches.length; i++)
    out.push(base + wrapPc(chord.pitches[i]))
  var kLow = 48
  var kHigh = 76
  while (out[out.length - 1] > kHigh && out[0] - 12 >= kLow) {
    for (i = 0; i < out.length; i++)
      out[i] -= 12
  }
  while (out[0] < kLow) {
    for (i = 0; i < out.length; i++)
      out[i] += 12
  }
  return out
}

function toTriadPayload(chord) {
  if (!chord)
    return null
  return { rootPc: wrapPc(chord.rootPc), quality: chord.quality }
}

function progressionEntry(modeIndex, degreeIndex) {
  return { modeIndex: modeIndex, degreeIndex: degreeIndex }
}

function resolveProgression(entries, rootPc, useSevenths) {
  var out = []
  var i
  for (i = 0; i < entries.length; i++) {
    var e = entries[i]
    out.push(cellChord(rootPc, e.modeIndex, e.degreeIndex, useSevenths))
  }
  return out
}

function shiftProgressionRows(entries, delta) {
  var out = []
  var i
  for (i = 0; i < entries.length; i++) {
    var next = entries[i].modeIndex + delta
    if (next < 0 || next >= MODE_NAMES.length)
      return null
    out.push({ modeIndex: next, degreeIndex: entries[i].degreeIndex })
  }
  return out
}

function transposeProgressionRoot(entries, oldRootPc, newRootPc) {
  if (!entries.length)
    return entries
  return entries.slice()
}
