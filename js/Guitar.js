.pragma library

// Standard-tuning guitar voicings (low E → high e). -1 = muted.
// Open / first-position shapes for major and minor; movable shapes for dim / aug.

var STRING_OPEN_MIDI = [40, 45, 50, 55, 59, 64]
var STRING_NAMES = ["E", "A", "D", "G", "B", "e"]
var EMPTY_FRETS = [-1, -1, -1, -1, -1, -1]

var MAJOR_FRETS = [
  [-1, 3, 2, 0, 1, 0],
  [-1, 4, 6, 6, 6, 4],
  [-1, -1, 0, 2, 3, 2],
  [-1, -1, 1, 3, 4, 3],
  [0, 2, 2, 1, 0, 0],
  [1, 3, 3, 2, 1, 1],
  [2, 4, 4, 3, 2, 2],
  [3, 2, 0, 0, 0, 3],
  [4, 6, 6, 5, 4, 4],
  [-1, 0, 2, 2, 2, 0],
  [-1, 1, 3, 3, 3, 1],
  [-1, 2, 4, 4, 4, 2]
]

var MINOR_FRETS = [
  [-1, 3, 5, 5, 4, 3],
  [-1, 4, 6, 6, 5, 4],
  [-1, -1, 0, 2, 3, 1],
  [-1, -1, 1, 3, 4, 2],
  [0, 2, 2, 0, 0, 0],
  [1, 3, 3, 1, 1, 1],
  [2, 4, 4, 2, 2, 2],
  [3, 5, 5, 3, 3, 3],
  [4, 6, 6, 4, 4, 4],
  [-1, 0, 2, 2, 1, 0],
  [-1, 1, 3, 3, 2, 1],
  [-1, 2, 4, 4, 3, 2]
]

function wrapPc(pc) {
  var n = Number(pc)
  if (!isFinite(n))
    return 0
  n = Math.floor(n) % 12
  return n < 0 ? n + 12 : n
}

function triadIntervals(quality) {
  if (quality === "minor")
    return [0, 3, 7]
  if (quality === "diminished")
    return [0, 3, 6]
  if (quality === "augmented")
    return [0, 4, 8]
  return [0, 4, 7]
}

function pitchClasses(rootPc, quality) {
  var root = wrapPc(rootPc)
  var iv = triadIntervals(quality)
  return [wrapPc(root + iv[0]), wrapPc(root + iv[1]), wrapPc(root + iv[2])]
}

function copyFrets(frets) {
  if (!frets || !frets.length)
    return EMPTY_FRETS.slice()
  return [frets[0], frets[1], frets[2], frets[3], frets[4], frets[5]]
}

function soundingPitchClasses(frets) {
  var pcs = []
  var i
  for (i = 0; i < 6; i++) {
    if (!frets || frets[i] < 0)
      continue
    var pc = (STRING_OPEN_MIDI[i] + Number(frets[i])) % 12
    if (pc < 0)
      pc += 12
    if (pcs.indexOf(pc) === -1)
      pcs.push(pc)
  }
  return pcs
}

function coversChord(frets, rootPc, quality) {
  var need = pitchClasses(rootPc, quality)
  var have = soundingPitchClasses(frets)
  var i
  for (i = 0; i < need.length; i++) {
    if (have.indexOf(need[i]) === -1)
      return false
  }
  return true
}

function dimFrets(rootPc) {
  var f = (wrapPc(rootPc) - 9 + 12) % 12
  return [-1, f, f + 1, f + 2, f + 1, -1]
}

function augFrets(rootPc) {
  var pc = wrapPc(rootPc)
  if (pc === 4)
    return [0, 3, 2, 1, 1, 0]
  if (pc === 7)
    return [3, 2, 1, 0, 0, 3]
  var f = pc
  return [-1, 3 + f, 2 + f, 1 + f, 1 + f, 0 + f]
}

function highestFret(frets) {
  var m = 0
  var i
  for (i = 0; i < 6; i++) {
    if (frets && frets[i] > m)
      m = frets[i]
  }
  return m
}

function tableFrets(rootPc, quality) {
  var pc = wrapPc(rootPc)
  if (quality === "minor")
    return copyFrets(MINOR_FRETS[pc])
  if (quality === "diminished")
    return dimFrets(pc)
  if (quality === "augmented")
    return augFrets(pc)
  return copyFrets(MAJOR_FRETS[pc])
}

function voicingFor(rootPc, quality) {
  var q = quality || "major"
  var pc = wrapPc(rootPc)
  var frets = tableFrets(pc, q)
  if (!coversChord(frets, pc, q) || highestFret(frets) > 12)
    frets = searchVoicing(pc, q) || EMPTY_FRETS.slice()
  return { rootPc: pc, quality: q, frets: frets }
}

function searchVoicing(rootPc, quality) {
  var need = pitchClasses(rootPc, quality)
  var best = null
  var bestScore = 1e9
  var acc = [-1, -1, -1, -1, -1, -1]

  function rec(stringIndex, minFret, maxFret, haveMask, bassPc) {
    if (stringIndex === 6) {
      if (haveMask !== 7)
        return
      var first = -1
      var last = -1
      var sounding = 0
      var i
      for (i = 0; i < 6; i++) {
        if (acc[i] < 0)
          continue
        if (first < 0)
          first = i
        last = i
        sounding += 1
      }
      if (sounding < 3)
        return
      for (i = first; i <= last; i++) {
        if (acc[i] < 0)
          return
      }
      var span = (minFret < 0 || maxFret < 0) ? 0 : maxFret - minFret
      if (span > 4)
        return
      var score = span * 12 + (minFret < 0 ? 0 : minFret) * 2
      if (bassPc !== wrapPc(rootPc))
        score += 10
      for (i = 0; i < 6; i++) {
        if (acc[i] < 0)
          score += 2
        else if (acc[i] === 0)
          score -= 1
      }
      if (score < bestScore) {
        bestScore = score
        best = acc.slice()
      }
      return
    }

    if (stringIndex <= 2 || stringIndex === 5) {
      acc[stringIndex] = -1
      rec(stringIndex + 1, minFret, maxFret, haveMask, bassPc)
    }

    var fret
    for (fret = 0; fret <= 12; fret++) {
      var midi = STRING_OPEN_MIDI[stringIndex] + fret
      var pc = midi % 12
      var tone = need.indexOf(pc)
      if (tone < 0)
        continue
      var nMin = minFret
      var nMax = maxFret
      if (fret > 0) {
        nMin = minFret < 0 ? fret : Math.min(minFret, fret)
        nMax = maxFret < 0 ? fret : Math.max(maxFret, fret)
        if (nMax - nMin > 4)
          continue
      }
      acc[stringIndex] = fret
      rec(
        stringIndex + 1,
        nMin,
        nMax,
        haveMask | (1 << tone),
        bassPc < 0 ? pc : bassPc
      )
    }
    acc[stringIndex] = -1
  }

  rec(0, -1, -1, 0, -1)
  return best
}

function fretGlyph(fret) {
  if (fret === undefined || fret === null || fret < 0)
    return "x"
  return String(fret)
}

function tabLine(stringName, fret) {
  var g = fretGlyph(fret)
  if (g.length === 1)
    return stringName + "|--" + g + "--"
  return stringName + "|--" + g + "-"
}

function tabLines(voicing, orientation) {
  var frets = voicing && voicing.frets ? voicing.frets : EMPTY_FRETS
  var lines = []
  var i
  for (i = 5; i >= 0; i--) {
    var name = STRING_NAMES[i]
    var fret = frets[i]
    var hasChord = !!(voicing && voicing.frets)
    lines.push({
      name: name,
      fret: hasChord ? fret : -1,
      glyph: hasChord ? fretGlyph(fret) : "-",
      text: hasChord ? tabLine(name, fret) : name + "|-----"
    })
  }
  if (orientation === "vertical")
    return rotateTabLinesClockwise(lines)
  return lines
}

// Horizontal rows (high e on top) → columns (low E on the left).
function rotateTabLinesClockwise(lines) {
  var out = []
  var i
  for (i = lines.length - 1; i >= 0; i--)
    out.push(lines[i])
  return out
}

function tabBlock(voicing, orientation) {
  var lines = tabLines(voicing, orientation)
  var i
  if (orientation === "vertical") {
    var names = []
    var glyphs = []
    for (i = 0; i < lines.length; i++) {
      names.push(lines[i].name)
      glyphs.push(lines[i].glyph)
    }
    return names.join(" ") + "\n" + glyphs.join(" ")
  }
  var out = []
  for (i = 0; i < lines.length; i++)
    out.push(lines[i].text)
  return out.join("\n")
}
