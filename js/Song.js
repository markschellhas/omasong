.pragma library

// Measures, slot spans, place/resize. Do not call
// Model.js helpers as globals — this file is a .pragma library in QML.

var BARS_PER_ROW = 4
var MAX_SECTIONS = 32
var MAX_MEASURES_PER_SECTION = 128
var MAX_TIME_NUMERATOR = 16
var MAX_SLOTS_PER_MEASURE = 16
var MAX_BEAT_STEPS = MAX_TIME_NUMERATOR * 8
var MAX_TITLE_LEN = 80
var MAX_ID_LEN = 64
var BEAT_LANES = ["kick", "snare", "hihat"]

function normalizeTitle(raw) {
  var t = typeof raw === "string" ? raw.trim() : ""
  if (!t) return "Untitled"
  if (t.length > MAX_TITLE_LEN) t = t.slice(0, MAX_TITLE_LEN)
  return t
}

function normalizeId(raw) {
  if (typeof raw !== "string") return ""
  var id = raw.trim()
  if (!id || id.length > MAX_ID_LEN) return ""
  return id
}

function spanOf(slot) {
  var n = slot && Number(slot.span)
  if (!isFinite(n) || n < 1)
    return 1
  return Math.floor(n)
}

function barCapacity(ts) {
  var n = ts && ts.numerator
  if (!(n >= 1))
    return 1
  return Math.min(MAX_SLOTS_PER_MEASURE, Math.floor(n))
}

function wrapPc(pc) {
  var m = pc % 12
  return m < 0 ? m + 12 : m
}

function cloneChord(chord) {
  if (!chord || typeof chord !== "object")
    return null
  var pc = Number(chord.rootPc)
  var quality = chord.quality
  if (!isFinite(pc) || typeof quality !== "string" || !quality)
    return null
  return { rootPc: wrapPc(Math.round(pc)), quality: quality }
}

function emptySlot(span) {
  return { chord: null, span: span > 0 ? span : 1 }
}

function beatStepCount(ts) {
  var normalized = normalizeTimeSig(ts)
  var count = Math.floor(normalized.numerator * 16 / normalized.denominator)
  return Math.max(1, Math.min(MAX_BEAT_STEPS, count))
}

function beatLaneValid(lane) {
  for (var i = 0; i < BEAT_LANES.length; i++) {
    if (BEAT_LANES[i] === lane)
      return true
  }
  return false
}

function normalizeBeatPattern(src, steps) {
  var pattern = {}
  var source = src && typeof src === "object" ? src : {}
  var count = Number(steps)
  if (!isFinite(count) || count < 1)
    count = 1
  count = Math.min(MAX_BEAT_STEPS, Math.floor(count))
  for (var li = 0; li < BEAT_LANES.length; li++) {
    var lane = BEAT_LANES[li]
    var values = Array.isArray(source[lane]) ? source[lane] : []
    var normalized = []
    for (var step = 0; step < count; step++)
      normalized.push(step < values.length && !!values[step])
    pattern[lane] = normalized
  }
  return pattern
}

function emptyBeatPattern(steps) {
  return normalizeBeatPattern(null, steps)
}

function emptyRun(slots, index, left) {
  var sum = 0
  var i
  if (left) {
    for (i = index - 1; i >= 0; i--) {
      if (slots[i].chord)
        break
      sum += spanOf(slots[i])
    }
  } else {
    for (i = index + 1; i < slots.length; i++) {
      if (slots[i].chord)
        break
      sum += spanOf(slots[i])
    }
  }
  return sum
}

function applyShrink(slots, sl, amount, fromLeft, capacity) {
  var slot = slots[sl]
  amount = Math.min(amount, spanOf(slot) - 1)
  if (amount <= 0)
    return

  slot.span = spanOf(slot) - amount

  var remaining = amount
  while (remaining > 0 && slots.length < capacity) {
    var insertAt = fromLeft ? sl : sl + 1
    slots.splice(insertAt, 0, emptySlot(1))
    if (fromLeft)
      sl++
    remaining--
  }

  if (remaining > 0) {
    var neighbor = fromLeft ? sl - 1 : sl + 1
    if (neighbor >= 0 && neighbor < slots.length && !slots[neighbor].chord)
      slots[neighbor].span = spanOf(slots[neighbor]) + remaining
    else
      slots[sl].span += remaining
  }
}

function applyGrow(slots, sl, amount, fromLeft) {
  while (amount > 0) {
    var neighbor = fromLeft ? sl - 1 : sl + 1
    if (neighbor < 0 || neighbor >= slots.length)
      break
    if (slots[neighbor].chord)
      break

    var nspan = spanOf(slots[neighbor])
    var take = Math.min(amount, nspan)
    if (take === nspan) {
      slots.splice(neighbor, 1)
      if (fromLeft)
        sl--
      slots[sl].span = spanOf(slots[sl]) + take
    } else {
      slots[neighbor].span = nspan - take
      slots[sl].span = spanOf(slots[sl]) + take
    }
    amount -= take
  }
}

function normalizeMeasure(measure, capacity, beatSteps) {
  capacity = Math.max(1, capacity)
  measure.beats = normalizeBeatPattern(measure.beats, beatSteps)
  if (!measure.slots || !measure.slots.length) {
    measure.slots = [emptySlot(capacity)]
    return
  }

  var i
  for (i = 0; i < measure.slots.length; i++)
    measure.slots[i].span = spanOf(measure.slots[i])

  while (measure.slots.length > capacity) {
    var empty = -1
    for (i = measure.slots.length - 1; i >= 0; i--) {
      if (!measure.slots[i].chord) {
        empty = i
        break
      }
    }
    if (empty >= 0)
      measure.slots.splice(empty, 1)
    else
      measure.slots.pop()
  }

  var sum = 0
  for (i = 0; i < measure.slots.length; i++)
    sum += measure.slots[i].span
  if (sum === capacity)
    return

  var n = measure.slots.length
  var leftover = capacity - n
  var spans = []
  for (i = 0; i < n; i++)
    spans.push(1)

  if (leftover > 0 && sum > 0) {
    var remainder = []
    var used = 0
    for (i = 0; i < n; i++) {
      var exact = leftover * measure.slots[i].span / sum
      var add = Math.floor(exact)
      spans[i] += add
      used += add
      remainder.push({ frac: exact - add, index: i })
    }
    remainder.sort(function (a, b) { return b.frac - a.frac })
    for (var k = 0; used < leftover && k < n; k++, used++)
      spans[remainder[k].index]++
  }

  for (i = 0; i < n; i++)
    measure.slots[i].span = spans[i]
}

function rowCount(measureCount) {
  if (measureCount <= 0)
    return 0
  return Math.floor((measureCount + BARS_PER_ROW - 1) / BARS_PER_ROW)
}

function rowIndexForMeasure(measureIndex) {
  if (measureIndex < 0)
    return 0
  return Math.floor(measureIndex / BARS_PER_ROW)
}

function syncRowRepeats(section) {
  var rows = rowCount(section.measures.length)
  if (!section.rowRepeats)
    section.rowRepeats = []
  while (section.rowRepeats.length > rows)
    section.rowRepeats.pop()
  while (section.rowRepeats.length < rows)
    section.rowRepeats.push(false)
}

function syncMeasuresToTimeSignature(section) {
  if (!section.measures)
    section.measures = []
  while (section.measures.length < BARS_PER_ROW)
    section.measures.push({ slots: [emptySlot(1)] })
  var cap = barCapacity(section.timeSig)
  var steps = beatStepCount(section.timeSig)
  for (var i = 0; i < section.measures.length; i++)
    normalizeMeasure(section.measures[i], cap, steps)
  syncRowRepeats(section)
}

function isMeasureEmpty(measure) {
  var slots = measure && measure.slots ? measure.slots : []
  for (var i = 0; i < slots.length; i++) {
    if (slots[i].chord)
      return false
  }
  return isBeatPatternEmpty(measure)
}

function isBeatPatternEmpty(value) {
  var pattern = value && value.beats ? value.beats : value
  pattern = pattern && typeof pattern === "object" ? pattern : {}
  for (var li = 0; li < BEAT_LANES.length; li++) {
    var values = Array.isArray(pattern[BEAT_LANES[li]]) ? pattern[BEAT_LANES[li]] : []
    for (var step = 0; step < values.length; step++) {
      if (values[step])
        return false
    }
  }
  return true
}

function normalizeTimeSig(ts) {
  var n = ts && Number(ts.numerator)
  var d = ts && Number(ts.denominator)
  if (!isFinite(n) || n < 1)
    n = 4
  else
    n = Math.min(MAX_TIME_NUMERATOR, Math.floor(n))
  if (d !== 2 && d !== 4 && d !== 8)
    d = 4
  return { numerator: n, denominator: d }
}

function sectionName(name) {
  if (name === undefined || name === null)
    return "Section"
  var s = String(name)
  return s ? s : "Section"
}

function makeSection(name, ts) {
  var section = {
    name: sectionName(name),
    timeSig: normalizeTimeSig(ts),
    measures: [],
    rowRepeats: []
  }
  syncMeasuresToTimeSignature(section)
  return section
}

function defaultSong() {
  var verse = makeSection("Verse")
  var chorus = makeSection("Chorus")
  verse.measures[0].slots[0].chord = { rootPc: 0, quality: "major" }
  verse.measures[1].slots[0].chord = { rootPc: 7, quality: "major" }
  verse.measures[2].slots[0].chord = { rootPc: 5, quality: "major" }
  verse.measures[3].slots[0].chord = { rootPc: 2, quality: "minor" }
  chorus.measures[0].slots[0].chord = { rootPc: 2, quality: "major" }
  chorus.measures[1].slots[0].chord = { rootPc: 7, quality: "major" }
  chorus.measures[2].slots[0].chord = { rootPc: 0, quality: "major" }
  chorus.measures[3].slots[0].chord = { rootPc: 4, quality: "minor" }
  return {
    title: "Untitled",
    id: "",
    bpm: 120,
    keyIndex: 0,
    beatsVisible: false,
    sections: [verse, chorus]
  }
}

function copyMeasure(src, cap, beatSteps) {
  var measure = { slots: [], beats: normalizeBeatPattern(src && src.beats, beatSteps) }
  var slots = src && Array.isArray(src.slots) ? src.slots : []
  for (var i = 0; i < slots.length; i++) {
    var sl = slots[i] || {}
    measure.slots.push({
      chord: cloneChord(sl.chord),
      span: spanOf(sl)
    })
  }
  if (!measure.slots.length)
    measure.slots.push(emptySlot(cap))
  return measure
}

function normalizeSection(src) {
  src = src || {}
  var section = {
    name: sectionName(typeof src.name === "string" && src.name.trim() ? src.name.trim() : "Section"),
    timeSig: normalizeTimeSig(src.timeSig),
    measures: [],
    rowRepeats: []
  }
  var cap = barCapacity(section.timeSig)
  var steps = beatStepCount(section.timeSig)
  var list = Array.isArray(src.measures) ? src.measures : []
  if (!list.length) {
    syncMeasuresToTimeSignature(section)
  } else {
    var measureLimit = Math.min(list.length, MAX_MEASURES_PER_SECTION)
    for (var i = 0; i < measureLimit; i++)
      section.measures.push(copyMeasure(list[i], cap, steps))
    for (var m = 0; m < section.measures.length; m++)
      normalizeMeasure(section.measures[m], cap, steps)
    syncRowRepeats(section)
  }
  if (Array.isArray(src.rowRepeats)) {
    for (var r = 0; r < section.rowRepeats.length && r < src.rowRepeats.length; r++)
      section.rowRepeats[r] = !!src.rowRepeats[r]
  }
  return section
}

function looksLikeSongDocument(raw) {
  if (!raw || !Array.isArray(raw.sections) || !raw.sections.length)
    return false
  var first = raw.sections[0] || {}
  return Array.isArray(first.measures)
}

function normalizeSong(raw) {
  var song = defaultSong()
  if (!raw || typeof raw !== "object")
    return song
  song.title = normalizeTitle(raw.title)
  song.id = normalizeId(raw.id)
  song.beatsVisible = !!raw.beatsVisible
  var bpm = Number(raw.bpm)
  if (isFinite(bpm))
    song.bpm = Math.max(40, Math.min(240, bpm))
  var key = Number(raw.keyIndex)
  if (isFinite(key))
    song.keyIndex = wrapPc(Math.round(key))
  if (!looksLikeSongDocument(raw))
    return song
  song.sections = []
  var sectionLimit = Math.min(raw.sections.length, MAX_SECTIONS)
  for (var i = 0; i < sectionLimit; i++)
    song.sections.push(normalizeSection(raw.sections[i]))
  if (!song.sections.length) {
    var fallback = defaultSong()
    fallback.title = song.title
    fallback.id = song.id
    fallback.beatsVisible = song.beatsVisible
    return fallback
  }
  return song
}

function cloneSong(song) {
  return normalizeSong(JSON.parse(JSON.stringify(song || defaultSong())))
}

function validSection(song, sectionIndex) {
  return !!(song && song.sections && sectionIndex >= 0 && sectionIndex < song.sections.length)
}

function validMeasure(song, sectionIndex, measureIndex) {
  if (!validSection(song, sectionIndex))
    return false
  var measures = song.sections[sectionIndex].measures
  return measureIndex >= 0 && measureIndex < measures.length
}

function validSlot(song, sectionIndex, measureIndex, slotIndex) {
  if (!validMeasure(song, sectionIndex, measureIndex))
    return false
  var slots = song.sections[sectionIndex].measures[measureIndex].slots
  return slotIndex >= 0 && slotIndex < slots.length
}

function getBeats(song, sectionIndex, measureIndex) {
  if (!validMeasure(song, sectionIndex, measureIndex))
    return { kick: [], snare: [], hihat: [] }
  var section = song.sections[sectionIndex]
  return normalizeBeatPattern(section.measures[measureIndex].beats, beatStepCount(section.timeSig))
}

function hasBeat(song, sectionIndex, measureIndex, lane, step) {
  if (!validMeasure(song, sectionIndex, measureIndex) || !beatLaneValid(lane))
    return false
  var index = Number(step)
  if (!isFinite(index) || index < 0 || Math.floor(index) !== index)
    return false
  var pattern = song.sections[sectionIndex].measures[measureIndex].beats
  return !!(pattern && Array.isArray(pattern[lane]) && index < pattern[lane].length && pattern[lane][index])
}

function toggleBeat(song, sectionIndex, measureIndex, lane, step) {
  var next = cloneSong(song)
  if (!validMeasure(next, sectionIndex, measureIndex) || !beatLaneValid(lane))
    return next
  var index = Number(step)
  var pattern = next.sections[sectionIndex].measures[measureIndex].beats
  if (!isFinite(index) || index < 0 || Math.floor(index) !== index || index >= pattern[lane].length)
    return next
  pattern[lane][index] = !pattern[lane][index]
  return next
}

function setBpm(song, bpm) {
  var next = cloneSong(song)
  var n = Number(bpm)
  if (!isFinite(n))
    return next
  next.bpm = Math.max(40, Math.min(240, n))
  return next
}

function addSection(song, name) {
  var next = cloneSong(song)
  if (next.sections.length >= MAX_SECTIONS)
    return next
  next.sections.push(makeSection(sectionName(name)))
  return next
}

function removeSection(song, sectionIndex) {
  var next = cloneSong(song)
  if (!validSection(next, sectionIndex) || next.sections.length <= 1)
    return next
  next.sections.splice(sectionIndex, 1)
  return next
}

function renameSection(song, sectionIndex, name) {
  var next = cloneSong(song)
  if (!validSection(next, sectionIndex))
    return next
  next.sections[sectionIndex].name = sectionName(name)
  return next
}

function setSectionName(song, sectionIndex, name) {
  return renameSection(song, sectionIndex, name)
}

function setTimeSignature(song, sectionIndex, ts) {
  var next = cloneSong(song)
  if (!validSection(next, sectionIndex))
    return next
  next.sections[sectionIndex].timeSig = normalizeTimeSig(ts)
  syncMeasuresToTimeSignature(next.sections[sectionIndex])
  return next
}

function addBars(song, sectionIndex, count) {
  var next = cloneSong(song)
  if (!validSection(next, sectionIndex))
    return next
  var n = Number(count)
  if (!isFinite(n) || n < 1)
    n = BARS_PER_ROW
  else
    n = Math.floor(n)
  var section = next.sections[sectionIndex]
  var room = MAX_MEASURES_PER_SECTION - section.measures.length
  if (room <= 0)
    return next
  if (n > room)
    n = room
  var cap = barCapacity(section.timeSig)
  var steps = beatStepCount(section.timeSig)
  for (var i = 0; i < n; i++)
    section.measures.push({ slots: [emptySlot(cap)], beats: emptyBeatPattern(steps) })
  syncRowRepeats(section)
  return next
}

function removeMeasure(song, sectionIndex, measureIndex) {
  var next = cloneSong(song)
  if (!validMeasure(next, sectionIndex, measureIndex))
    return next
  var section = next.sections[sectionIndex]
  if (section.measures.length <= BARS_PER_ROW)
    return next
  if (!isMeasureEmpty(section.measures[measureIndex]))
    return next
  section.measures.splice(measureIndex, 1)
  syncRowRepeats(section)
  return next
}

function addSlot(song, sectionIndex, measureIndex) {
  var next = cloneSong(song)
  if (!validMeasure(next, sectionIndex, measureIndex))
    return next
  var slots = next.sections[sectionIndex].measures[measureIndex].slots
  var cap = barCapacity(next.sections[sectionIndex].timeSig)
  if (slots.length >= cap)
    return next
  var idx = -1
  for (var i = slots.length - 1; i >= 0; i--) {
    if (spanOf(slots[i]) >= 2) {
      idx = i
      break
    }
  }
  if (idx < 0)
    return next
  var newSpan = Math.floor(spanOf(slots[idx]) / 2)
  slots[idx].span = spanOf(slots[idx]) - newSpan
  slots.splice(idx + 1, 0, emptySlot(newSpan))
  return next
}

function setChord(song, sectionIndex, measureIndex, slotIndex, chord) {
  var next = cloneSong(song)
  if (!validSlot(next, sectionIndex, measureIndex, slotIndex))
    return next
  next.sections[sectionIndex].measures[measureIndex].slots[slotIndex].chord = cloneChord(chord)
  return next
}

function getChord(song, sectionIndex, measureIndex, slotIndex) {
  if (!validSlot(song, sectionIndex, measureIndex, slotIndex))
    return null
  return cloneChord(song.sections[sectionIndex].measures[measureIndex].slots[slotIndex].chord)
}

function slotSpan(song, sectionIndex, measureIndex, slotIndex) {
  if (!validSlot(song, sectionIndex, measureIndex, slotIndex))
    return 0
  return spanOf(song.sections[sectionIndex].measures[measureIndex].slots[slotIndex])
}

function canSplitSlot(song, sectionIndex, measureIndex, slotIndex) {
  if (!validSlot(song, sectionIndex, measureIndex, slotIndex))
    return false
  var slots = song.sections[sectionIndex].measures[measureIndex].slots
  var slot = slots[slotIndex]
  return !!slot.chord && spanOf(slot) >= 2 && slots.length < barCapacity(song.sections[sectionIndex].timeSig)
}

function emptySpanOnSide(song, sectionIndex, measureIndex, slotIndex, left) {
  if (!validSlot(song, sectionIndex, measureIndex, slotIndex))
    return 0
  return emptyRun(song.sections[sectionIndex].measures[measureIndex].slots, slotIndex, !!left)
}

function slotSpanSum(measure) {
  var slots = measure && measure.slots ? measure.slots : []
  var sum = 0
  for (var i = 0; i < slots.length; i++)
    sum += spanOf(slots[i])
  return sum
}

function extractSlotChord(slots, slotIndex, capacity) {
  var slot = slots[slotIndex]
  if (!slot || !slot.chord)
    return null
  var chord = cloneChord(slot.chord)
  var freed = spanOf(slot)
  slots.splice(slotIndex, 1)
  if (!slots.length) {
    slots.push(emptySlot(capacity))
    return chord
  }
  if (slotIndex < slots.length)
    slots[slotIndex].span = spanOf(slots[slotIndex]) + freed
  else
    slots[slotIndex - 1].span = spanOf(slots[slotIndex - 1]) + freed
  return chord
}

function moveChord(song, fromSection, fromMeasure, fromSlot, toSection, toMeasure, toSlot, insertAfter) {
  var next = cloneSong(song)
  if (!validSlot(next, fromSection, fromMeasure, fromSlot))
    return next
  if (!validSlot(next, toSection, toMeasure, toSlot))
    return next
  if (fromSection === toSection && fromMeasure === toMeasure && fromSlot === toSlot)
    return next

  var fromSlots = next.sections[fromSection].measures[fromMeasure].slots
  var cap = barCapacity(next.sections[fromSection].timeSig)
  var chord = extractSlotChord(fromSlots, fromSlot, cap)
  if (!chord)
    return next

  var targetSlot = toSlot
  if (fromSection === toSection && fromMeasure === toMeasure && fromSlot < toSlot)
    targetSlot--

  if (!validSlot(next, toSection, toMeasure, targetSlot))
    return next
  next = placeChord(next, toSection, toMeasure, targetSlot, chord, insertAfter)
  return next
}

function placeChord(song, sectionIndex, measureIndex, slotIndex, chord, insertAfter) {
  var next = cloneSong(song)
  if (!validSlot(next, sectionIndex, measureIndex, slotIndex))
    return next
  var incoming = cloneChord(chord)
  if (!incoming)
    return next

  var slots = next.sections[sectionIndex].measures[measureIndex].slots
  var slot = slots[slotIndex]

  if (!slot.chord) {
    slot.chord = incoming
    return next
  }
  if (!canSplitSlot(next, sectionIndex, measureIndex, slotIndex)) {
    slot.chord = incoming
    return next
  }

  var newSpan = Math.floor(spanOf(slot) / 2)
  slot.span = spanOf(slot) - newSpan
  var extra = { chord: incoming, span: newSpan }
  if (insertAfter)
    slots.splice(slotIndex + 1, 0, extra)
  else
    slots.splice(slotIndex, 0, extra)
  return next
}

function fromLeftEdge(edge) {
  return edge === true || edge === "left"
}

function resizeSlot(song, sectionIndex, measureIndex, slotIndex, newSpan, edge) {
  var next = cloneSong(song)
  if (!validSlot(next, sectionIndex, measureIndex, slotIndex))
    return next
  var fromLeft = fromLeftEdge(edge)
  var slots = next.sections[sectionIndex].measures[measureIndex].slots
  var oldSpan = spanOf(slots[slotIndex])
  var maxSpan = oldSpan + emptyRun(slots, slotIndex, fromLeft)
  var span = Number(newSpan)
  if (!isFinite(span))
    return next
  span = Math.round(span)
  if (span < 1)
    span = 1
  if (span > maxSpan)
    span = maxSpan
  if (span === oldSpan)
    return next
  var cap = barCapacity(next.sections[sectionIndex].timeSig)
  if (span < oldSpan)
    applyShrink(slots, slotIndex, oldSpan - span, fromLeft, cap)
  else
    applyGrow(slots, slotIndex, span - oldSpan, fromLeft)
  return next
}

function setRowRepeat(song, sectionIndex, rowIndex, shouldRepeat) {
  var next = cloneSong(song)
  if (!validSection(next, sectionIndex))
    return next
  var section = next.sections[sectionIndex]
  syncRowRepeats(section)
  if (rowIndex < 0 || rowIndex >= section.rowRepeats.length)
    return next
  section.rowRepeats[rowIndex] = !!shouldRepeat
  return next
}

function slotDurationBeats(span, denominator) {
  var d = Number(denominator)
  if (!isFinite(d) || d < 1)
    d = 4
  return spanOf({ span: span }) * (4 / d)
}

function slotDurationBeatsAt(song, sectionIndex, measureIndex, slotIndex) {
  if (!validSlot(song, sectionIndex, measureIndex, slotIndex))
    return 0
  var section = song.sections[sectionIndex]
  var slot = section.measures[measureIndex].slots[slotIndex]
  return slotDurationBeats(spanOf(slot), section.timeSig && section.timeSig.denominator)
}

function appendMeasure(events, beat, section, si, mi, repeatPass) {
  var measure = section.measures[mi]
  var slots = measure && measure.slots ? measure.slots : []
  var denom = section.timeSig && section.timeSig.denominator
  for (var sl = 0; sl < slots.length; sl++) {
    var slot = slots[sl]
    var dur = slotDurationBeats(spanOf(slot), denom)
    var chord = cloneChord(slot.chord)
    events.push({
      startBeat: beat,
      durationBeats: dur,
      chord: chord,
      rest: !chord,
      sectionIndex: si,
      measureIndex: mi,
      slotIndex: sl,
      repeatPass: repeatPass
    })
    beat += dur
  }
  return beat
}

function buildSectionTimeline(song, sectionIndex) {
  var events = []
  var beat = 0
  if (!song || !song.sections)
    return events
  var si = Number(sectionIndex)
  if (!isFinite(si) || si < 0 || si >= song.sections.length)
    return events
  var section = song.sections[si]
  var n = section.measures ? section.measures.length : 0
  var rows = rowCount(n)
  var flags = section.rowRepeats || []
  for (var row = 0; row < rows; row++) {
    var start = row * BARS_PER_ROW
    var end = Math.min(start + BARS_PER_ROW, n)
    var repeats = row < flags.length && flags[row]
    var passes = repeats ? 2 : 1
    for (var pass = 0; pass < passes; pass++) {
      for (var mi = start; mi < end; mi++)
        beat = appendMeasure(events, beat, section, si, mi, pass)
    }
  }
  return events
}

function buildTimeline(song) {
  var events = []
  var beat = 0
  if (!song || !song.sections)
    return events
  for (var si = 0; si < song.sections.length; si++) {
    var sectionEvents = buildSectionTimeline(song, si)
    for (var i = 0; i < sectionEvents.length; i++) {
      var e = sectionEvents[i]
      events.push({
        startBeat: beat + e.startBeat,
        durationBeats: e.durationBeats,
        chord: e.chord,
        rest: e.rest,
        sectionIndex: e.sectionIndex,
        measureIndex: e.measureIndex,
        slotIndex: e.slotIndex,
        repeatPass: e.repeatPass
      })
    }
    if (sectionEvents.length) {
      var last = sectionEvents[sectionEvents.length - 1]
      beat += last.startBeat + last.durationBeats
    }
  }
  return events
}

function beatsToSeconds(beats, bpm) {
  var b = Number(beats)
  var p = Number(bpm)
  if (!isFinite(b) || b < 0)
    b = 0
  if (!isFinite(p) || p < 1)
    p = 120
  return b * (60 / p)
}

function timelineDurationBeats(events) {
  if (!events || !events.length)
    return 0
  var last = events[events.length - 1]
  return last.startBeat + last.durationBeats
}

function isMeasureStartEvent(events, event) {
  if (!events || !events.length || !event)
    return false
  for (var i = 0; i < events.length; i++) {
    var candidate = events[i]
    if (candidate.sectionIndex === event.sectionIndex
        && candidate.measureIndex === event.measureIndex
        && candidate.repeatPass === event.repeatPass)
      return candidate.startBeat === event.startBeat
        && candidate.slotIndex === event.slotIndex
  }
  return false
}

function eventAtBeat(events, beat) {
  if (!events || !events.length)
    return null
  var t = Number(beat)
  if (!isFinite(t) || t < 0)
    t = 0
  for (var i = 0; i < events.length; i++) {
    var e = events[i]
    if (t >= e.startBeat && t < e.startBeat + e.durationBeats)
      return e
  }
  return null
}

function beatTickDelta(events, beat) {
  var event = eventAtBeat(events, beat)
  if (!event)
    return 0
  var remaining = event.startBeat + event.durationBeats - beat
  var onInteger = Math.abs(beat - Math.round(beat)) < 1e-9
  var nextInteger = onInteger ? Math.round(beat) + 1 : Math.ceil(beat)
  var toInteger = nextInteger - beat
  var delta = Math.min(1, remaining, toInteger)
  return delta > 0 ? delta : 0
}
