// Loaded into a VM with Model/Song/Agent/Keyboard/Focus functions in scope.

assertEq(PC_NAMES.join(" "), "C Db D Eb E F F# G Ab A Bb B")
assertEq(station(0).major, "C")
assertEq(station(0).relativeMinor, "Am")
assertEq(station(1).major, "G")
assertEq(station(11).major, "F")
assertEq(chordName(0, "major"), "C")
assertEq(chordName(0, "minor"), "Cm")
assertEq(chordName(0, "diminished"), "Cdim")
assertEq(chordName(0, "augmented"), "Caug")
assertEq(qualityInt("major"), 0)
assertEq(qualityInt("minor"), 1)
assertEq(qualityInt("diminished"), 2)
assertEq(qualityInt("augmented"), 3)
assertEq(encodeChord({ rootPc: 0, quality: "major" }), "chord|C|0|0")
assertEq(decodeChord("chord|Dm|2|1").rootPc, 2)
assertEq(decodeChord("chord|Dm|2|1").quality, "minor")
var dia = diatonicTriads(0)
assertEq(dia.length, 7)
assertEq(chordName(dia[0].rootPc, dia[0].quality), "C")
assertEq(chordName(dia[1].rootPc, dia[1].quality), "Dm")
assertEq(chordName(dia[6].rootPc, dia[6].quality), "Bdim")
assertEq(numeralFor(dia[0], 0), "I")
assertEq(maxSlots({ numerator: 4, denominator: 4 }), 4)
assertEq(maxSlots({ numerator: 3, denominator: 4 }), 3)
assertEq(maxSlots({ numerator: 2, denominator: 4 }), 2)
assertEq(maxSlots({ numerator: 6, denominator: 8 }), 6)
assertEq(beatsPerBar({ numerator: 4, denominator: 4 }), 4)
assertEq(beatsPerBar({ numerator: 6, denominator: 8 }), 3)
var midi = triadMidi({ rootPc: 0, quality: "major" })
assertEq(midi.length, 3)
assert(midi[0] >= 48 && midi[2] <= 72, "voiced in C3–C5")

// Polar / wedge helpers used by CircleOfFifths.qml (rotated key at 12 o'clock).
assertEq(wrap(12), 0, "wrap 12")
assertEq(wrap(-1), 11, "wrap -1")
assertEq(wrap(0 + 1), 1)
assertEq(wrap(0 - 1), 11)
assertEq(rotate(0, 1), 1)
assertEq(rotate(0, -1), 11)
assertEq(rotate(11, 1), 0)
assertEq(rotate(1, -1), 0)
assertEq(tonicPc(0), 0)
assertEq(tonicPc(1), 7)
assertEq(tonicPc(11), 5)
assertEq(keyIndexFromPc(0), 0)
assertEq(keyIndexFromPc(7), 1)
assertEq(keyIndexFromPc(5), 11)
assertEq(keyIndexFromPc(1), 7, "Db is key 7")
var ki
for (ki = 0; ki < 12; ki++)
  assertEq(keyIndexFromPc(tonicPc(ki)), ki, "keyIndexFromPc roundtrip " + ki)
var pcRound
for (pcRound = 0; pcRound < 12; pcRound++)
  assertEq(tonicPc(keyIndexFromPc(pcRound)), pcRound, "tonicPc roundtrip " + pcRound)
assertEq(visualSector(0, 0), 0)
assertEq(visualSector(1, 1), 0)
assertEq(visualSector(0, 1), 11)
var hitTopC = hitTest(100, 10, 100, 100, 20, 40, 50, 95, 0)
assertEq(hitTopC.ring, "major")
assertEq(hitTopC.index, 0)
var hitTopG = hitTest(100, 10, 100, 100, 20, 40, 50, 95, 1)
assertEq(hitTopG.index, 1)
assertEq(keyAt(0).major, "C")
assertEq(keyAt(1).major, "G")
assertEq(label(0), "C / Am")
assert(inKeyWedge(0, 0), "tonic in wedge")
assert(inKeyWedge(1, 0), "dominant in wedge")
assert(inKeyWedge(11, 0), "subdominant in wedge")
assert(!inKeyWedge(2, 0), "D not in C wedge")
assertEq(triad(0, "major").label, "C")
assertEq(triad(0, "minor").label, "Am")
assertEq(triad(0, "major").notes.length, 3)
var selectedC = { rootPc: 0, quality: "major" }
var previewG = { rootPc: 7, quality: "major" }
var playF = { rootPc: 5, quality: "major" }
assertEq(resolveDisplayChord(false, null, null, selectedC).rootPc, 0)
assertEq(resolveDisplayChord(false, null, previewG, selectedC).rootPc, 7, "circle preview sticks over selected slot")
assertEq(resolveDisplayChord(false, null, previewG, selectedC).rootPc, 7, "preview still wins after audition notes clear")
assertEq(resolveDisplayChord(true, playF, previewG, selectedC).rootPc, 5)
assertEq(resolveDisplayChord(false, playF, previewG, selectedC).rootPc, 7, "after stop, circle preview remains")
assertEq(resolveDisplayChord(false, null, null, null), null)
assertEq(triad(0, "major").rootPc, 0)
assertEq(triad(0, "major").quality, "major")
assertEq(triad(0, "minor").rootPc, 9)
assertEq(triad(0, "minor").quality, "minor")

var blank = emptySong()
assertEq(blank.title, "Untitled")
assertEq(blank.id, "")
assertEq(blank.bpm, 120)
assertEq(blank.keyIndex, 0)
assertEq(blank.beatsVisible, false)
assertEq(blank.sections.length, 2)
assertEq(blank.sections[0].name, "Verse")
assertEq(blank.sections[1].name, "Chorus")
assertEq(blank.sections[0].measures.length, 4)
assertEq(blank.sections[0].measures[0].slots[0].chord, null)
assert(isMeasureEmpty(blank.sections[0].measures[0]), "new project verse is empty")
assert(isMeasureEmpty(blank.sections[1].measures[0]), "new project chorus is empty")
var blankNorm = normalizeSong(blank)
assertEq(blankNorm.title, "Untitled")
assertEq(blankNorm.id, "")
assertEq(blankNorm.sections[0].measures[0].slots[0].chord, null)

var song = defaultSong()
assertEq(song.bpm, 120)
assertEq(song.keyIndex, 0)
assertEq(song.title, "Untitled")
assertEq(song.id, "")
assertEq(song.sections.length, 2)
assertEq(song.sections[0].name, "Verse")
assertEq(song.sections[1].name, "Chorus")
assertEq(song.sections[0].timeSig.numerator, 4)
assertEq(song.sections[0].timeSig.denominator, 4)
assertEq(song.sections[0].measures.length, 4)
assertEq(song.sections[1].measures.length, 4)
assertEq(song.sections[0].measures[0].slots.length, 1)
assertEq(song.sections[0].measures[0].slots[0].span, 4)
assertEq(song.sections[0].rowRepeats.length, 1)
assertEq(song.sections[0].rowRepeats[0], false)
assertEq(sequencerStepWidth(820, 16, 24), 51.25)
assertEq(sequencerStepWidth(820, 128, 24), 24)
assertEq(sequencerStepWidth(0, 0, 0), 1)
assertEq(sequencerFocusCount(16, 3), 50)
assertEq(sequencerFocusCount(128, 3), 386)
assertEq(sequencerNextFocusIndex(49, 1, 16, 3), 0)
assertEq(sequencerNextFocusIndex(0, -1, 16, 3), 49)
assertEq(sequencerNextFocusIndex(385, 1, 128, 3), 0)
assertEq(beatAsciiRow([true, false, false, true], "x", "-"), "x--x")
assertEq(beatAsciiRow([false, false, false, false], "x", "-"), "----")
assertEq(beatAsciiRow([], "x", "-"), "")
assertEq(beatAsciiRow(null, "x", "-"), "")
assertEq(beatAsciiRow([true, false], "", ""), "x-")
// QML hands model-derived lanes over as sequence wrappers: array-like, but
// Array.isArray() is false for them. beatAsciiRow must still render those.
var wrappedLane = { length: 4, 0: true, 1: false, 2: false, 3: true }
assertEq(Array.isArray(wrappedLane), false)
assertEq(beatAsciiRow(wrappedLane, "x", "-"), "x--x")
assertEq(beatRowLength(wrappedLane), 4)
assertEq(beatRowLength([true, false, true]), 3)
assertEq(beatRowLength(null), 0)
assertEq(beatRowLength("xxxx"), 0)
assertEq(beatRowLength({}), 0)
assertEq(patternHasHit({ kick: [false, false], snare: [], hihat: [] }), false)
assertEq(patternHasHit({ kick: [false, true], snare: [], hihat: [] }), true)
assertEq(patternHasHit({ kick: [], snare: [], hihat: [true] }), true)
assertEq(patternHasHit({ kick: { length: 2, 0: false, 1: true } }), true)
assertEq(patternHasHit(null), false)
assertEq(patternHasHit({}), false)

// copyBeatsToNext: within a section, fresh arrays, bounds-checked
var copySrc = normalizeSong({
  sections: [{
    name: "Verse",
    timeSig: { numerator: 4, denominator: 4 },
    measures: [
      { slots: [{ span: 4 }], beats: { kick: [true], snare: [], hihat: [true] } },
      { slots: [{ span: 4 }], beats: { snare: [true] } },
      { slots: [{ span: 4 }], beats: {} }
    ]
  }]
})
assertEq(canCopyBeatsToNext(copySrc, 0, 0), true)
assertEq(canCopyBeatsToNext(copySrc, 0, 2), false)   // last bar in section
assertEq(canCopyBeatsToNext(copySrc, 0, 9), false)   // out of range
var copied = copyBeatsToNext(copySrc, 0, 0)
assertEq(copied.sections[0].measures[1].beats.kick[0], true)
assertEq(copied.sections[0].measures[1].beats.hihat[0], true)
assertEq(copied.sections[0].measures[1].beats.snare[0], false)  // overwritten
assertEq(copied.sections[0].measures[1].beats.kick.length, 16)
// source untouched, and the two bars must not share arrays
assertEq(copySrc.sections[0].measures[1].beats.kick[0], false)
var copiedThenToggled = toggleBeat(copied, 0, 1, "kick", 4)
assertEq(copiedThenToggled.sections[0].measures[1].beats.kick[4], true)
assertEq(copiedThenToggled.sections[0].measures[0].beats.kick[4], false)
// copying from the last bar is a no-op
assertEq(isBeatPatternEmpty(copyBeatsToNext(copySrc, 0, 2).sections[0].measures[2].beats), true)

// copyBeatsToRest: fills every later bar in the section
var filled = copyBeatsToRest(copySrc, 0, 0)
assertEq(filled.sections[0].measures[1].beats.kick[0], true)
assertEq(filled.sections[0].measures[2].beats.kick[0], true)
assertEq(filled.sections[0].measures[1].beats.hihat[0], true)
assertEq(filled.sections[0].measures[2].beats.hihat[0], true)
assertEq(filled.sections[0].measures[1].beats.snare[0], false)
assertEq(filled.sections[0].measures[2].beats.kick.length, 16)
// source untouched and no two bars share a pattern
assertEq(copySrc.sections[0].measures[2].beats.kick.length, 16)
assertEq(isBeatPatternEmpty(copySrc.sections[0].measures[2].beats), true)
var filledThenToggled = toggleBeat(filled, 0, 1, "kick", 7)
assertEq(filledThenToggled.sections[0].measures[1].beats.kick[7], true)
assertEq(filledThenToggled.sections[0].measures[2].beats.kick[7], false)
assertEq(filledThenToggled.sections[0].measures[0].beats.kick[7], false)
// filling from the last bar, or out of range, changes nothing
assertEq(isBeatPatternEmpty(copyBeatsToRest(copySrc, 0, 2).sections[0].measures[2].beats), true)
assertEq(copyBeatsToRest(copySrc, 0, 9).sections[0].measures[1].beats.snare[0], true)
// filling from the middle leaves earlier bars alone
var midFilled = copyBeatsToRest(copyBeatsToNext(copySrc, 0, 0), 0, 1)
assertEq(midFilled.sections[0].measures[2].beats.kick[0], true)
assertEq(midFilled.sections[0].measures[0].beats.kick[0], true)
assertEq(BEAT_LANES.join(","), "kick,snare,hihat")
assertEq(beatStepCount({ numerator: 4, denominator: 4 }), 16)
assertEq(beatStepCount({ numerator: 3, denominator: 4 }), 12)
assertEq(beatStepCount({ numerator: 6, denominator: 8 }), 12)
assertEq(song.beatsVisible, false)
assertEq(getBeats(song, 0, 0).kick.length, 16)
assertEq(getBeats(song, 0, 0).snare.length, 16)
assertEq(getBeats(song, 0, 0).hihat.length, 16)
assert(isBeatPatternEmpty(getBeats(song, 0, 0)), "default beat pattern is empty")

// Legacy and malformed beat patterns normalize to meter-sized booleans.
var legacyBeats = normalizeSong({
  beatsVisible: true,
  sections: [{
    name: "Legacy",
    timeSig: { numerator: 3, denominator: 4 },
    measures: [{ slots: [{ chord: null, span: 3 }] }]
  }]
})
assertEq(legacyBeats.beatsVisible, true)
assertEq(getBeats(legacyBeats, 0, 0).kick.length, 12)
assert(isBeatPatternEmpty(getBeats(legacyBeats, 0, 0)), "legacy beat pattern is empty")
var malformedBeats = []
for (var mbi = 0; mbi < 300; mbi++) malformedBeats.push(mbi === 1 ? 1 : 0)
var normalizedBeats = normalizeSong({
  sections: [{
    name: "Odd meter",
    timeSig: { numerator: 99, denominator: 2 },
    measures: [{
      slots: [{ chord: null, span: 16 }],
      beats: { kick: malformedBeats, snare: "invalid", hihat: [null, "hit"] }
    }]
  }]
})
var safeBeats = getBeats(normalizedBeats, 0, 0)
assertEq(safeBeats.kick.length, MAX_BEAT_STEPS)
assertEq(safeBeats.snare.length, MAX_BEAT_STEPS)
assertEq(safeBeats.hihat.length, MAX_BEAT_STEPS)
assertEq(safeBeats.kick[0], false)
assertEq(safeBeats.kick[1], true)
assertEq(safeBeats.snare[0], false)
assertEq(safeBeats.hihat[1], true)

// Toggling is immutable and affects only the requested bar, lane, and step.
var beatToggled = toggleBeat(song, 0, 1, "snare", 4)
assertEq(hasBeat(beatToggled, 0, 1, "snare", 4), true)
assertEq(hasBeat(song, 0, 1, "snare", 4), false)
assertEq(hasBeat(beatToggled, 0, 0, "snare", 4), false)
assertEq(hasBeat(beatToggled, 0, 1, "kick", 4), false)
assertEq(hasBeat(beatToggled, 0, 1, "snare", 5), false)
assertEq(hasBeat(toggleBeat(beatToggled, 0, 1, "snare", 4), 0, 1, "snare", 4), false)
assertEq(hasBeat(toggleBeat(song, 99, 0, "kick", 0), 0, 0, "kick", 0), false)
assertEq(hasBeat(toggleBeat(song, 0, 0, "tom", 0), 0, 0, "kick", 0), false)
assertEq(hasBeat(toggleBeat(song, 0, 0, "kick", 999), 0, 0, "kick", 0), false)

// Clear is immutable and empties only the requested bar at its meter-aware size.
var beatsToClear = toggleBeat(toggleBeat(song, 0, 1, "kick", 0), 0, 1, "hihat", 15)
beatsToClear = toggleBeat(beatsToClear, 0, 2, "snare", 4)
var beatsCleared = clearBeats(beatsToClear, 0, 1)
assert(isBeatPatternEmpty(getBeats(beatsCleared, 0, 1)), "clearBeats empties requested bar")
assertEq(getBeats(beatsCleared, 0, 1).kick.length, 16)
assertEq(hasBeat(beatsCleared, 0, 2, "snare", 4), true)
assertEq(hasBeat(beatsToClear, 0, 1, "kick", 0), true)
assert(beatsCleared.sections[0].measures[1].beats !== beatsToClear.sections[0].measures[1].beats,
       "clearBeats owns its beat pattern")
assertEq(hasBeat(clearBeats(beatsToClear, 99, 0), 0, 1, "kick", 0), true)
var threeFourClear = toggleBeat(legacyBeats, 0, 0, "snare", 11)
threeFourClear = clearBeats(threeFourClear, 0, 0)
assertEq(getBeats(threeFourClear, 0, 0).snare.length, 12)
assert(isBeatPatternEmpty(getBeats(threeFourClear, 0, 0)), "clearBeats keeps meter size")

// Clone, bar creation, trimming, and meter resizing retain beat content.
var beatClone = cloneSong(beatToggled)
assertEq(hasBeat(beatClone, 0, 1, "snare", 4), true)
assert(beatClone.sections[0].measures[1].beats !== beatToggled.sections[0].measures[1].beats,
       "clone owns its beat pattern")
var beatEight = addBars(toggleBeat(song, 0, 0, "kick", 0), 0)
assertEq(getBeats(beatEight, 0, 7).kick.length, 16)
assert(isBeatPatternEmpty(getBeats(beatEight, 0, 7)), "new bar beat pattern is empty")
var beatOnLast = toggleBeat(beatEight, 0, 7, "hihat", 15)
assertEq(removeMeasure(beatOnLast, 0, 7).sections[0].measures.length, 8)
var resizedBeats = toggleBeat(toggleBeat(song, 0, 0, "kick", 2), 0, 0, "kick", 14)
resizedBeats = setTimeSignature(resizedBeats, 0, { numerator: 3, denominator: 4 })
assertEq(getBeats(resizedBeats, 0, 0).kick.length, 12)
assertEq(hasBeat(resizedBeats, 0, 0, "kick", 2), true)
resizedBeats = setTimeSignature(resizedBeats, 0, { numerator: 6, denominator: 8 })
assertEq(getBeats(resizedBeats, 0, 0).kick.length, 12)
resizedBeats = setTimeSignature(resizedBeats, 0, { numerator: 4, denominator: 4 })
assertEq(getBeats(resizedBeats, 0, 0).kick.length, 16)
assertEq(hasBeat(resizedBeats, 0, 0, "kick", 2), true)
assertEq(hasBeat(resizedBeats, 0, 0, "kick", 14), false)
assertEq(cloneSong(legacyBeats).beatsVisible, true)

// title / id normalize + round-trip through cloneSong
assertEq(normalizeTitle(null), "Untitled")
assertEq(normalizeTitle("  "), "Untitled")
assertEq(normalizeTitle("  Demo  "), "Demo")
assertEq(normalizeId(null), "")
assertEq(normalizeId(12), "")
assertEq(normalizeId("  "), "")
assertEq(normalizeId("  abc-123  "), "abc-123")
var longTitle = ""
for (var ti = 0; ti < 100; ti++) longTitle += "x"
assertEq(normalizeTitle(longTitle).length, MAX_TITLE_LEN)
var longId = ""
for (var ii = 0; ii < 97; ii++) longId += "a"
assertEq(normalizeId(longId), "")
var maxId = longId.slice(0, MAX_ID_LEN)
assertEq(normalizeId(maxId), maxId)
var titled = normalizeSong({
  title: "  My Song  ",
  id: "550e8400-e29b-41d4-a716-446655440000",
  bpm: 120,
  keyIndex: 0,
  sections: song.sections
})
assertEq(titled.title, "My Song")
assertEq(titled.id, "550e8400-e29b-41d4-a716-446655440000")
assertEq(normalizeSong({ title: longTitle, sections: song.sections }).title.length, MAX_TITLE_LEN)
assertEq(normalizeSong({ id: longId, sections: song.sections }).id, "")
assertEq(normalizeSong({ title: null, id: null, sections: song.sections }).title, "Untitled")
assertEq(normalizeSong({ title: null, id: null, sections: song.sections }).id, "")
var clonedMeta = cloneSong(titled)
assertEq(clonedMeta.title, "My Song")
assertEq(clonedMeta.id, "550e8400-e29b-41d4-a716-446655440000")
assertEq(chordName(song.sections[0].measures[0].slots[0].chord.rootPc, song.sections[0].measures[0].slots[0].chord.quality), "C")
assertEq(chordName(song.sections[0].measures[1].slots[0].chord.rootPc, song.sections[0].measures[1].slots[0].chord.quality), "G")
assertEq(chordName(song.sections[0].measures[2].slots[0].chord.rootPc, song.sections[0].measures[2].slots[0].chord.quality), "F")
assertEq(chordName(song.sections[0].measures[3].slots[0].chord.rootPc, song.sections[0].measures[3].slots[0].chord.quality), "Dm")
assertEq(chordName(song.sections[1].measures[0].slots[0].chord.rootPc, song.sections[1].measures[0].slots[0].chord.quality), "D")
assertEq(chordName(song.sections[1].measures[1].slots[0].chord.rootPc, song.sections[1].measures[1].slots[0].chord.quality), "G")
assertEq(chordName(song.sections[1].measures[2].slots[0].chord.rootPc, song.sections[1].measures[2].slots[0].chord.quality), "C")
assertEq(chordName(song.sections[1].measures[3].slots[0].chord.rootPc, song.sections[1].measures[3].slots[0].chord.quality), "Em")
assertEq(rowCount(4), 1)
assertEq(rowCount(6), 2)
assertEq(rowIndexForMeasure(3), 0)
assertEq(rowIndexForMeasure(4), 1)
assertEq(slotSpan(song, 0, 0, 0), 4)
assert(canSplitSlot(song, 0, 0, 0), "full chord can split")

// removeSection is a no-op only for the last remaining section.
assertEq(removeSection(song, 0).sections.length, 1)
assertEq(removeSection(song, 0).sections[0].name, "Chorus")
assertEq(song.sections.length, 2)
assertEq(song.sections[0].name, "Verse")
var one = removeSection(removeSection(addSection(song, "Bridge"), 2), 1)
assertEq(one.sections.length, 1)
assertEq(one.sections[0].name, "Verse")
assertEq(removeSection(one, 0).sections.length, 1)
var bridge = addSection(song, "Bridge")
assertEq(bridge.sections.length, 3)
assertEq(bridge.sections[2].name, "Bridge")
assertEq(bridge.sections[2].measures.length, 4)
assertEq(bridge.sections[2].measures[0].slots[0].chord, null)
assertEq(bridge.sections[2].measures[0].slots[0].span, 4)
assertEq(addSection(song, "").sections[2].name, "Section")
var capped = song
for (var si = 0; si < 40; si++)
  capped = addSection(capped, "S" + si)
assertEq(capped.sections.length, MAX_SECTIONS)
var hugeBars = addBars(cloneSong(song), 0, 500)
assert(hugeBars.sections[0].measures.length <= MAX_MEASURES_PER_SECTION)
var hugeSig = setTimeSignature(cloneSong(song), 0, { numerator: 99, denominator: 4 })
assertEq(hugeSig.sections[0].timeSig.numerator, MAX_TIME_NUMERATOR)

var s3 = setTimeSignature(cloneSong(song), 0, { numerator: 3, denominator: 4 })
assertEq(s3.sections[0].measures.length, 4)
assertEq(slotSpanSum(s3.sections[0].measures[0]), 3)
assertEq(slotSpan(s3, 0, 0, 0), 3)
var s4sig = setTimeSignature(s3, 0, { numerator: 4, denominator: 4 })
assertEq(s4sig.sections[0].measures.length, 4)
assertEq(s4sig.sections[0].rowRepeats.length, 1)
var six = setTimeSignature(cloneSong(song), 0, { numerator: 6, denominator: 8 })
assertEq(six.sections[0].measures.length, 4)
assertEq(six.sections[0].rowRepeats.length, 1)
assertEq(slotSpanSum(six.sections[0].measures[0]), 6)

var eight = addBars(cloneSong(song), 0)
assertEq(eight.sections[0].measures.length, 8)
assertEq(eight.sections[0].rowRepeats.length, 2)
assertEq(eight.sections[0].measures[7].slots[0].chord, null)
assertEq(removeMeasure(eight, 0, 7).sections[0].measures.length, 7)
assertEq(removeMeasure(eight, 0, 0).sections[0].measures.length, 8)
var trimmed = removeMeasure(removeMeasure(removeMeasure(removeMeasure(eight, 0, 7), 0, 6), 0, 5), 0, 4)
assertEq(trimmed.sections[0].measures.length, 4)
assertEq(removeMeasure(trimmed, 0, 3).sections[0].measures.length, 4)

var placed = placeChord(cloneSong(song), 0, 0, 0, { rootPc: 7, quality: "major" }, false)
assert(placed.sections[0].measures[0].slots[0].chord.rootPc === 7)
var split = placeChord(cloneSong(song), 0, 0, 0, { rootPc: 7, quality: "major" }, true)
assert(split.sections[0].measures[0].slots.length >= 2)
assertEq(slotSpanSum(split.sections[0].measures[0]), 4)
var resized = resizeSlot(cloneSong(song), 0, 0, 0, 2, "right")
assertEq(slotSpanSum(resized.sections[0].measures[0]), 4)
var cleared = setChord(cloneSong(song), 0, 0, 0, null)
assertEq(cleared.sections[0].measures[0].slots[0].chord, null)

// placeChord edges: split, insert side, max-capacity replace.
var sPlace = cloneSong(song)
sPlace = placeChord(sPlace, 0, 0, 0, { rootPc: 5, quality: "major" }, true)
assertEq(sPlace.sections[0].measures[0].slots.length, 2)
assertEq(chordName(sPlace.sections[0].measures[0].slots[0].chord.rootPc, sPlace.sections[0].measures[0].slots[0].chord.quality), "C")
assertEq(chordName(sPlace.sections[0].measures[0].slots[1].chord.rootPc, sPlace.sections[0].measures[0].slots[1].chord.quality), "F")
assertEq(slotSpan(sPlace, 0, 0, 0), 2)
assertEq(slotSpan(sPlace, 0, 0, 1), 2)
sPlace = placeChord(sPlace, 0, 0, 0, { rootPc: 7, quality: "major" }, false)
assertEq(sPlace.sections[0].measures[0].slots.length, 3)
assertEq(chordName(sPlace.sections[0].measures[0].slots[0].chord.rootPc, sPlace.sections[0].measures[0].slots[0].chord.quality), "G")
assertEq(slotSpan(sPlace, 0, 0, 0), 1)
assertEq(slotSpan(sPlace, 0, 0, 1), 1)
assertEq(slotSpan(sPlace, 0, 0, 2), 2)
sPlace = placeChord(sPlace, 0, 0, 2, { rootPc: 2, quality: "minor" }, true)
assertEq(sPlace.sections[0].measures[0].slots.length, 4)
sPlace = placeChord(sPlace, 0, 0, 0, { rootPc: 2, quality: "major" }, true)
assertEq(sPlace.sections[0].measures[0].slots.length, 4)
assertEq(chordName(sPlace.sections[0].measures[0].slots[0].chord.rootPc, sPlace.sections[0].measures[0].slots[0].chord.quality), "D")

var emptyBar = setChord(cloneSong(song), 0, 0, 0, null)
var filledEmpty = placeChord(emptyBar, 0, 0, 0, { rootPc: 0, quality: "major" }, true)
assertEq(filledEmpty.sections[0].measures[0].slots.length, 1)
assertEq(filledEmpty.sections[0].measures[0].slots[0].chord.rootPc, 0)

// moveChord: drag a placed chord to either side of another.
var splitBar = placeChord(cloneSong(song), 0, 0, 0, { rootPc: 5, quality: "major" }, true)
assertEq(chordName(splitBar.sections[0].measures[0].slots[0].chord.rootPc, splitBar.sections[0].measures[0].slots[0].chord.quality), "C")
assertEq(chordName(splitBar.sections[0].measures[0].slots[1].chord.rootPc, splitBar.sections[0].measures[0].slots[1].chord.quality), "F")
var movedBefore = moveChord(splitBar, 0, 0, 1, 0, 0, 0, false)
assertEq(chordName(movedBefore.sections[0].measures[0].slots[0].chord.rootPc, movedBefore.sections[0].measures[0].slots[0].chord.quality), "F")
assertEq(chordName(movedBefore.sections[0].measures[0].slots[1].chord.rootPc, movedBefore.sections[0].measures[0].slots[1].chord.quality), "C")
var movedAfter = moveChord(splitBar, 0, 0, 0, 0, 0, 1, true)
assertEq(chordName(movedAfter.sections[0].measures[0].slots[0].chord.rootPc, movedAfter.sections[0].measures[0].slots[0].chord.quality), "F")
assertEq(chordName(movedAfter.sections[0].measures[0].slots[1].chord.rootPc, movedAfter.sections[0].measures[0].slots[1].chord.quality), "C")
var crossBar = moveChord(cloneSong(song), 0, 0, 0, 0, 1, 0, false)
assertEq(crossBar.sections[0].measures[0].slots[0].chord, null)
assertEq(chordName(crossBar.sections[0].measures[1].slots[0].chord.rootPc, crossBar.sections[0].measures[1].slots[0].chord.quality), "C")
assertEq(chordName(crossBar.sections[0].measures[1].slots[1].chord.rootPc, crossBar.sections[0].measures[1].slots[1].chord.quality), "G")
assertEq(moveChord(song, 0, 0, 0, 0, 0, 0, true).sections[0].measures[0].slots[0].chord.rootPc, 0)

// resizeSlot: shrink opens unit empties; grow absorbs them.
var sResize = resizeSlot(cloneSong(song), 0, 0, 0, 2, "right")
assertEq(sResize.sections[0].measures[0].slots.length, 3)
assertEq(chordName(sResize.sections[0].measures[0].slots[0].chord.rootPc, sResize.sections[0].measures[0].slots[0].chord.quality), "C")
assertEq(slotSpan(sResize, 0, 0, 0), 2)
assertEq(sResize.sections[0].measures[0].slots[1].chord, null)
assertEq(sResize.sections[0].measures[0].slots[2].chord, null)
assertEq(slotSpan(sResize, 0, 0, 1), 1)
assertEq(slotSpan(sResize, 0, 0, 2), 1)
sResize = resizeSlot(sResize, 0, 0, 0, 1, "right")
assertEq(sResize.sections[0].measures[0].slots.length, 4)
assertEq(emptySpanOnSide(sResize, 0, 0, 0, false), 3)
sResize = resizeSlot(sResize, 0, 0, 0, 3, "right")
assertEq(sResize.sections[0].measures[0].slots.length, 2)
assertEq(slotSpan(sResize, 0, 0, 0), 3)
assertEq(sResize.sections[0].measures[0].slots[1].chord, null)

var sLeft = resizeSlot(cloneSong(song), 0, 0, 0, 2, "left")
assertEq(sLeft.sections[0].measures[0].slots.length, 3)
assertEq(sLeft.sections[0].measures[0].slots[0].chord, null)
assertEq(sLeft.sections[0].measures[0].slots[1].chord, null)
assertEq(chordName(sLeft.sections[0].measures[0].slots[2].chord.rootPc, sLeft.sections[0].measures[0].slots[2].chord.quality), "C")

var sMeter = setTimeSignature(cloneSong(song), 0, { numerator: 3, denominator: 4 })
sMeter = resizeSlot(sMeter, 0, 0, 0, 1, "right")
assertEq(sMeter.sections[0].measures[0].slots.length, 3)
sMeter = addSlot(sMeter, 0, 0)
assertEq(sMeter.sections[0].measures[0].slots.length, 3)

assertEq(setBpm(cloneSong(song), 96).bpm, 96)
assertEq(setBpm(cloneSong(song), 10).bpm, 40)
assertEq(setBpm(cloneSong(song), 300).bpm, 240)

var splitBefore = song.sections[0].measures[1].slots.length
var added = addSlot(cloneSong(song), 0, 1)
assertEq(added.sections[0].measures[1].slots.length, splitBefore + 1)

assertEq(semitoneForKey("a"), 0)
assertEq(semitoneForKey("w"), 1)
assertEq(semitoneForKey("s"), 2)
assertEq(semitoneForKey("j"), 11)
assertEq(semitoneForKey("k"), 12)
assertEq(semitoneForKey("z"), -1)
assertEq(midiForLaptopKey("a", 4), 60)
assertEq(midiForLaptopKey("w", 4), 61)
assertEq(midiForLaptopKey("k", 4), 72)
var keys = pianoKeysC3C5()
assertEq(keys[0].midi, 48)
assertEq(keys[keys.length - 1].midi, 72)
assertEq(wrapInstrument(-1), 2)
assertEq(wrapInstrument(3), 0)
assertEq(clampInstrument(4), 2)
assertEq(instrumentName(1), "Electric Piano")
assertEq(instrumentName(2), "Organ")
assertEq(shiftOctave(4, 1), 5)
assertEq(shiftOctave(8, 1), 8)
assertEq(shiftOctave(0, -1), 0)
assertEq(clampMidi(midiForLaptopKey("a", 0)), midiForLaptopKey("a", 0))

var song = defaultSong()
var tl = buildTimeline(song)
assertEq(tl.length, 8)
assertEq(tl[0].durationBeats, 4)
assertEq(tl[0].rest, false)
assertEq(beatsToSeconds(4, 120), 2)
assertEq(beatsToSeconds(1, 60), 1)
assertEq(timelineDurationBeats(tl), 32)
var verseTl = buildSectionTimeline(song, 0)
assertEq(verseTl.length, 4)
assertEq(timelineDurationBeats(verseTl), 16)
assertEq(verseTl[0].sectionIndex, 0)
assertEq(verseTl[verseTl.length - 1].sectionIndex, 0)
var chorusTl = buildSectionTimeline(song, 1)
assertEq(chorusTl.length, 4)
assertEq(timelineDurationBeats(chorusTl), 16)
assertEq(chorusTl[0].sectionIndex, 1)
assertEq(buildSectionTimeline(song, -1).length, 0)
assertEq(buildSectionTimeline(song, 99).length, 0)
assertEq(eventAtBeat(tl, 0).measureIndex, 0)
assertEq(eventAtBeat(tl, 4).measureIndex, 1)
assertEq(eventAtBeat(tl, 31).sectionIndex, 1)
var beats = 0
for (var i = 0; i < tl.length; i++) beats += tl[i].durationBeats
assertEq(beats, 32)
var restTl = buildTimeline(setChord(cloneSong(song), 0, 0, 0, null))
assertEq(restTl[0].rest, true)
assertEq(restTl[0].durationBeats, 4)
assert(restTl[0].measureStart, "rest measure has a launch point")
assertEq(typeof beatAtWallClock, "function")
assertEq(beatAtWallClock(1000, 1000, 120), 0)
assertEq(beatAtWallClock(1000, 1500, 120), 1)
assertEq(beatAtWallClock(1000, 2000, 120), 2)
assertEq(beatAtWallClock(1000, 500, 120), 0, "before start stays at 0")
assertEq(beatAtWallClock(0, 1000, 60), 1)

var defaultTl = buildTimeline(defaultSong())
assert(defaultTl[0].measureAudio, "every measure freezes an audio spec")
assertEq(defaultTl[0].measureAudio.chords.length, 1)
assertEq(defaultTl[0].patternedMeasure, false)
assertEq(defaultTl[0].measureAudio.beats.kick.length, 16)

var launches = measureLaunchEvents(defaultTl)
assertEq(launches.length, 8)
assertEq(launches[0].startBeat, 0)
assertEq(launches[1].startBeat, 4)
assert(launches[0].measureAudio.chords[0].chord)

var restSong = setChord(cloneSong(defaultSong()), 0, 0, 0, null)
var restLaunch = measureLaunchEvents(buildTimeline(restSong))[0]
assertEq(restLaunch.measureAudio.chords.length, 0, "rest measure still launches silence")
assertEq(restLaunch.measureStart, true)
var splitMeasure = resizeSlot(cloneSong(song), 0, 0, 0, 2, "right")
var splitMeasureTl = buildTimeline(splitMeasure)
var measureLaunches = 0
for (var launchIndex = 0; launchIndex < splitMeasureTl.length; launchIndex++) {
  if (splitMeasureTl[launchIndex].measureStart)
    measureLaunches++
}
assertEq(measureLaunches, 8, "whole-song playback launches once per measure")
assertEq(splitMeasureTl[0].patternedMeasure, false)
assertEq(splitMeasureTl[1].measureAudio, null, "only the measure start carries the spec")
var patternedTimeline = buildTimeline(toggleBeat(splitMeasure, 0, 0, "kick", 0))
assertEq(patternedTimeline[0].patternedMeasure, true)
assertEq(patternedTimeline[1].patternedMeasure, true, "all events suppress separate audio in patterned measure")
assertEq(patternedTimeline[3].patternedMeasure, false, "empty beat pattern stays unpatterned")
assert(patternedTimeline[3].measureAudio, "unpatterned measure still freezes chords for the engine")
assert(patternedTimeline[0].measureAudio, "patterned measure freezes a combined audio spec")
assertEq(patternedTimeline[1].measureAudio, null, "only the measure start carries the combined audio spec")
assertEq(patternedTimeline[0].measureAudio.steps, 16)
assertEq(patternedTimeline[0].measureAudio.beats.kick[0], true)
assertEq(patternedTimeline[0].measureAudio.chords.length, 1)
assertEq(patternedTimeline[0].measureAudio.chords[0].chord.rootPc, 0)
var editedAfterPlay = toggleBeat(splitMeasure, 0, 0, "kick", 0)
var frozenTimeline = buildTimeline(editedAfterPlay)
editedAfterPlay = toggleBeat(editedAfterPlay, 0, 0, "kick", 0)
editedAfterPlay = setChord(editedAfterPlay, 0, 0, 0, { rootPc: 7, quality: "major" })
assertEq(isBeatPatternEmpty(getBeats(editedAfterPlay, 0, 0)), true)
assertEq(frozenTimeline[0].patternedMeasure, true, "frozen playback keeps patterned suppression")
assertEq(frozenTimeline[0].measureAudio.beats.kick[0], true, "frozen playback keeps cleared beat")
assertEq(frozenTimeline[0].measureAudio.chords[0].chord.rootPc, 0, "frozen playback keeps edited chord")
var sectionLaunches = 0
var splitSectionTl = buildSectionTimeline(splitMeasure, 0)
for (launchIndex = 0; launchIndex < splitSectionTl.length; launchIndex++) {
  if (splitSectionTl[launchIndex].measureStart)
    sectionLaunches++
}
assertEq(sectionLaunches, 4, "section playback launches once per measure")
var loopLaunches = 0
for (var loopPass = 0; loopPass < 2; loopPass++) {
  if (eventAtBeat(splitMeasureTl, 0).measureStart)
    loopLaunches++
}
assertEq(loopLaunches, 2, "loop reset relaunches the first measure")
var walked = 0
var lastStart = -1
for (var b = 0; b < timelineDurationBeats(tl); b++) {
  var ev = eventAtBeat(tl, b)
  assert(ev, "event at beat " + b)
  if (ev.startBeat !== lastStart) {
    walked++
    lastStart = ev.startBeat
  }
}
assertEq(walked, 8)
assertEq(eventAtBeat(tl, timelineDurationBeats(tl)), null)
var repeated = setRowRepeat(cloneSong(song), 0, 0, true)
var tl2 = buildTimeline(repeated)
assertEq(tl2.length, 12)
beats = 0
for (i = 0; i < tl2.length; i++) beats += tl2[i].durationBeats
assertEq(beats, 48)
assertEq(tl2[4].repeatPass, 1)
assert(tl2[4].measureStart, "row-repeat pass has its own launch point")
var repeatedLaunches = 0
for (launchIndex = 0; launchIndex < tl2.length; launchIndex++) {
  if (tl2[launchIndex].measureStart)
    repeatedLaunches++
}
assertEq(repeatedLaunches, 12, "each row-repeat pass launches each measure once")
var repeatedSplitTl = buildTimeline(setRowRepeat(cloneSong(splitMeasure), 0, 0, true))
assert(repeatedSplitTl[6].measureStart, "split measure launches on repeat pass")
assertEq(repeatedSplitTl[7].measureStart, false, "later slot does not relaunch repeated measure")
assertEq(repeatedSplitTl[6].measureOffsetBeats, 0)
assert(repeatedSplitTl[7].measureOffsetBeats > 0, "later slot has a measure-relative offset")
var six = setTimeSignature(cloneSong(song), 0, { numerator: 6, denominator: 8 })
assertEq(six.sections[0].rowRepeats.length, 1)
assertEq(slotDurationBeats(4, 4), 4)
assertEq(slotDurationBeats(2, 4), 2)
assertEq(slotDurationBeats(1, 4), 1)
assertEq(slotDurationBeats(3, 4), 3)
assertEq(slotDurationBeats(4, 0), 4)
assertEq(slotDurationBeats(4, -1), 4)
assertEq(slotDurationBeatsAt(song, 0, 0, 0), 4)
var splitDur = resizeSlot(cloneSong(song), 0, 0, 0, 2, "right")
assertEq(slotDurationBeatsAt(splitDur, 0, 0, 0), 2)
assertEq(slotDurationBeatsAt(splitDur, 0, 0, 1), 1)
var threeFour = setTimeSignature(cloneSong(song), 0, { numerator: 3, denominator: 4 })
assertEq(slotDurationBeatsAt(threeFour, 0, 0, 0), 3)
assertEq(slotDurationBeatsAt(song, -1, 0, 0), 0)
assertEq(slotDurationBeatsAt(song, 0, 99, 0), 0)
assertEq(slotDurationBeatsAt(song, 0, 0, 99), 0)
assertEq(beatsToSeconds(4, 120), 2)
assertEq(beatsToSeconds(2, 120), 1)
assertEq(slotDurationBeats(6, 8), 3)
assertEq(slotDurationBeats(1, 8), 0.5)
assertEq(six.sections[0].measures[0].slots[0].span, 6)
assertEq(buildTimeline(six)[0].durationBeats, 3)
var sixSplit = resizeSlot(cloneSong(six), 0, 0, 0, 1, "right")
assertEq(sixSplit.sections[0].measures[0].slots[0].span, 1)
var sixTl = buildTimeline(sixSplit)
assertEq(sixTl[0].durationBeats, 0.5)
assertEq(sixTl[1].startBeat, 0.5)
var walkBeat = 0
var walkHits = 0
while (walkBeat < timelineDurationBeats(sixTl)) {
  var walkEv = eventAtBeat(sixTl, walkBeat)
  assert(walkEv, "eventAtBeat at " + walkBeat)
  assertEq(walkEv.startBeat, sixTl[walkHits].startBeat)
  walkHits++
  walkBeat = walkEv.startBeat + walkEv.durationBeats
}
assertEq(walkHits, sixTl.length)
for (var ei = 0; ei < sixTl.length; ei++) {
  var atStart = eventAtBeat(sixTl, sixTl[ei].startBeat)
  assertEq(atStart.startBeat, sixTl[ei].startBeat)
  assertEq(atStart.slotIndex, sixTl[ei].slotIndex)
}
assertEq(eventAtBeat(sixTl, 0.5).startBeat, 0.5)
assertEq(beatTickDelta(tl, 0), 1)
assertEq(beatTickDelta(tl, 3), 1)
assertEq(beatTickDelta(sixTl, 0), 0.5)
assertEq(beatTickDelta(sixTl, 0.5), 0.5)
var clockDisplay = []
var clockBeat = 0
while (clockBeat < 4) {
  clockDisplay.push(Math.floor(clockBeat) + 1)
  clockBeat += beatTickDelta(tl, clockBeat)
}
assertEq(clockDisplay.join(","), "1,2,3,4")
var clockHits = {}
clockBeat = 0
while (clockBeat < timelineDurationBeats(sixTl)) {
  clockHits[String(eventAtBeat(sixTl, clockBeat).startBeat)] = true
  clockBeat += beatTickDelta(sixTl, clockBeat)
}
assert(clockHits["0.5"], "beat clock hits 0.5")
assertEq(beatTickDelta([{ startBeat: 0, durationBeats: 4 }], 0), 1)
assertEq(beatTickDelta([{ startBeat: 0.5, durationBeats: 1.5 }], 0.5), 0.5)
assertEq(beatTickDelta([{ startBeat: 0.5, durationBeats: 0.5 }], 0.5), 0.5)
var sixTwo = resizeSlot(cloneSong(six), 0, 0, 0, 3, "right")
sixTwo = resizeSlot(sixTwo, 0, 0, 1, 3, "right")
assertEq(sixTwo.sections[0].measures[0].slots.length, 2)
assertEq(sixTwo.sections[0].measures[0].slots[0].span, 3)
assertEq(sixTwo.sections[0].measures[0].slots[1].span, 3)
var twoTl = buildTimeline(sixTwo)
assertEq(twoTl[0].durationBeats, 1.5)
assertEq(twoTl[1].startBeat, 1.5)
assertEq(twoTl[1].durationBeats, 1.5)
var twoClock = []
var twoBeat = 0
while (twoBeat < 3) {
  twoClock.push(twoBeat)
  twoBeat += beatTickDelta(twoTl, twoBeat)
}
twoClock.push(twoBeat)
assertEq(twoClock.join(","), "0,1,1.5,2,3")

// Region focus cycle (j down, k up, wrap).
assertEq(cycleNavRegion(0, 1), 1)
assertEq(cycleNavRegion(2, 1), 0)
assertEq(cycleNavRegion(0, -1), 2)
assertEq(regionName(0), "Circle of fifths")
assertEq(regionName(1), "Song structure")
assertEq(regionName(2), "Keyboard")
assertEq(degreeIndexFromKey(0x31, "1"), 0)
assertEq(degreeIndexFromKey(0x37, "7"), 6)
assertEq(degreeIndexFromKey(0x01000033, "3"), 2)
assertEq(degreeIndexFromKey(0x48, "h"), -1)
assertEq(degreeIndexFromKey(0x30, "0"), -1)
assertEq(degreeIndexFromKey(0x38, "8"), -1)
assertEq(degreeIndexFromKey(0x31, ""), 0)
assertEq(degreeIndexFromKey(NaN, "x"), -1)

var cI = previewHighlight(0, 0)
assertEq(cI.degree, 0)
assertEq(cI.index, 0)
assertEq(cI.ring, "major")
var cIi = previewHighlight(0, 1)
assertEq(cIi.index, 11)
assertEq(cIi.ring, "minor")
var cIii = previewHighlight(0, 2)
assertEq(cIii.index, 1)
assertEq(cIii.ring, "minor")
var cIV = previewHighlight(0, 3)
assertEq(cIV.index, 11)
assertEq(cIV.ring, "major")
var cV = previewHighlight(0, 4)
assertEq(cV.index, 1)
assertEq(cV.ring, "major")
var cVi = previewHighlight(0, 5)
assertEq(cVi.index, 0)
assertEq(cVi.ring, "minor")
var cVii = previewHighlight(0, 6)
assertEq(cVii.degree, 6)
assertEq(cVii.index, -1)
assertEq(cVii.ring, "")
assertEq(previewHighlight(0, -1).degree, -1)
assertEq(previewHighlight(0, 7).degree, -1)
assertEq(previewHighlight(0, "nope").degree, -1)

var gI = previewHighlight(1, 0)
assertEq(gI.index, 1)
assertEq(gI.ring, "major")
assertEq(previewHighlight(1, 1).index, 0)
assertEq(previewHighlight(1, 1).ring, "minor")
assertEq(previewHighlight(1, 4).index, 2)
assertEq(previewHighlight(1, 4).ring, "major")

var fromWedgeV = previewHighlightFromWedge(0, 1, "major")
assertEq(fromWedgeV.degree, 4)
assertEq(fromWedgeV.index, 1)
assertEq(fromWedgeV.ring, "major")
var fromWedgeAm = previewHighlightFromWedge(0, 0, "minor")
assertEq(fromWedgeAm.degree, 5)
assertEq(fromWedgeAm.ring, "minor")
var fromWedgeD = previewHighlightFromWedge(0, 2, "major")
assertEq(fromWedgeD.degree, -1)
assertEq(fromWedgeD.index, 2)
assertEq(fromWedgeD.ring, "major")
assertEq(wedgeChords(0).length, 6)
assertEq(wedgeChordByDegree(0, 1).roman, "I")
assertEq(wedgeChordByDegree(0, 5).roman, "V")
assertEq(wedgeChordByDegree(0, 7), null)

assert(shouldSpawnPreviewAudio(0, 1000), "first preview always plays")
assert(shouldSpawnPreviewAudio(1000, 1100), "gap of 100ms allows audio")
assert(!shouldSpawnPreviewAudio(1000, 1099), "sub-100ms is rate limited")
assert(!shouldSpawnPreviewAudio(1000, 1000), "same timestamp is limited")
assert(!shouldSpawnPreviewAudio(1000, NaN), "invalid now is denied")
assert(shouldSpawnPreviewAudio(1000, 1050, 40), "custom gap respected")

assertEq(sanitizeMidiNotes([60, 64, 67]).join(","), "60,64,67")
assertEq(sanitizeMidiNotes([60, 60, 64]).join(","), "60,64")
assertEq(sanitizeMidiNotes([-1, 128, 200, "x"]).length, 0)
assertEq(sanitizeMidiNotes([48, 52, 55, 60, 64, 67, 72, 76, 79]).length, 8)
assertEq(clampSeconds(0.7), 0.7)
assertEq(clampSeconds(100), 30)
assertEq(clampSeconds(-1), 0.7)
assertEq(clampSeconds("nope"), 0.7)
assertEq(clampSeconds(0.01), 0.05)

// Guitar tab voicings (standard tuning, low E → high e).
function assertFrets(rootPc, quality, expected, label) {
  var v = voicingFor(rootPc, quality)
  assertEq(v.frets.join(","), expected.join(","), label)
  assert(coversChord(v.frets, rootPc, quality), label + " covers triad")
}
assertFrets(0, "major", [-1, 3, 2, 0, 1, 0], "C")
assertFrets(7, "major", [3, 2, 0, 0, 0, 3], "G")
assertFrets(5, "major", [1, 3, 3, 2, 1, 1], "F")
assertFrets(2, "major", [-1, -1, 0, 2, 3, 2], "D")
assertFrets(9, "major", [-1, 0, 2, 2, 2, 0], "A")
assertFrets(4, "major", [0, 2, 2, 1, 0, 0], "E")
assertFrets(2, "minor", [-1, -1, 0, 2, 3, 1], "Dm")
assertFrets(4, "minor", [0, 2, 2, 0, 0, 0], "Em")
assertFrets(9, "minor", [-1, 0, 2, 2, 1, 0], "Am")
assertEq(tabBlock(voicingFor(0, "major")), "e|--0--\nB|--1--\nG|--0--\nD|--2--\nA|--3--\nE|--x--")
assertEq(tabBlock(null), "e|-----\nB|-----\nG|-----\nD|-----\nA|-----\nE|-----")
assertEq(tabBlock(voicingFor(0, "major"), "vertical"), "E A D G B e\nx 3 2 0 1 0")
assertEq(tabBlock(null, "vertical"), "E A D G B e\n- - - - - -")
assertEq(tabLines(voicingFor(0, "major"), "vertical")[0].name, "E")
assertEq(tabLines(voicingFor(0, "major"), "vertical")[5].name, "e")
assertEq(WHITE_KEYS_C3_C5, 15)
assertEq(pianoKeysC3C5().filter(function (k) { return k.type === "white" }).length, 15)
assertEq(pianoKeysC3C5().length, 25)
var qualities = ["major", "minor", "diminished", "augmented"]
var qi
var pc
for (qi = 0; qi < qualities.length; qi++) {
  for (pc = 0; pc < 12; pc++) {
    var found = voicingFor(pc, qualities[qi])
    assert(found.frets.length === 6, qualities[qi] + " " + pc + " has 6 strings")
    assert(coversChord(found.frets, pc, qualities[qi]), qualities[qi] + " " + pc + " voicing")
  }
}

// Parallel-mode colour grid.
var cPhryg2 = scaleNotes(0, 5)[1]
assertEq(cPhryg2.name, "Db", "C Phrygian 2nd is Db not C#")
var cLyd4 = scaleNotes(0, 0)[3]
assertEq(cLyd4.name, "F#", "C Lydian 4th is F#")
var ionianI = cellChord(0, 1, 0, false)
assertEq(ionianI.symbol, "C")
assertEq(romanNumeral(ionianI, 0, 1), "I")
var mixoI7 = cellChord(0, 2, 0, true)
assertEq(mixoI7.symbol, "C7", "Mixolydian tonic is dominant 7")
var ionianI7 = cellChord(0, 1, 0, true)
assertEq(ionianI7.symbol, "Cmaj7", "Ionian tonic is major 7")
var aeolian6 = cellChord(0, 4, 5, false)
assertEq(romanNumeral(aeolian6, 0, 1), "♭VI", "Aeolian vi relative to Ionian home")
var locTonic = cellChord(0, 6, 0, false)
assert(locTonic.unstableTonic, "Locrian tonic is diminished")
var grid4 = buildGrid(0, 1, false, false)
assertEq(grid4.length, 4, "compact view shows four modes")
var grid7 = buildGrid(0, 1, false, true)
assertEq(grid7.length, 7)
var fCount = 0
var r, c
for (r = 0; r < grid7.length; r++) {
  for (c = 0; c < grid7[r].cells.length; c++) {
    if (grid7[r].cells[c].chord.symbol === "F")
      fCount++
  }
}
assertEq(fCount, 3, "F major appears in three mode rows on C root")
var shifted = shiftProgressionRows(
  [{ modeIndex: 1, degreeIndex: 0 }, { modeIndex: 1, degreeIndex: 3 }], 1)
assertEq(shifted[0].modeIndex, 2)
assertEq(shifted[1].degreeIndex, 3)
var brightenIonian = nextHomeMode(1, -1, false)
assertEq(brightenIonian.homeModeIndex, 0)
assertEq(brightenIonian.showAllModes, true, "brighten from Ionian reveals Lydian")
var darkenIonian = nextHomeMode(1, 1, false)
assertEq(darkenIonian.homeModeIndex, 2)
assertEq(darkenIonian.showAllModes, false, "Mixolydian stays in four-mode view")
assertEq(nextHomeMode(0, -1, true), null, "Lydian cannot brighten further")
assertEq(nextHomeMode(6, 1, true), null, "Locrian cannot darken further")
var darkenAeolian = nextHomeMode(4, 1, false)
assertEq(darkenAeolian.homeModeIndex, 5)
assertEq(darkenAeolian.showAllModes, true, "darken from Aeolian reveals Phrygian")
assertEq(clampHomeToVisible(0, false), 1, "Lydian clamps to Ionian in four-mode view")
assertEq(clampHomeToVisible(5, false), 4, "Phrygian clamps to Aeolian")
assertEq(clampHomeToVisible(6, false), 4, "Locrian clamps to Aeolian")
assertEq(clampHomeToVisible(1, false), 1)
assertEq(clampHomeToVisible(0, true), 0)
assertEq(sharedToneCount(ionianI, cellChord(0, 1, 3, false)), 1)
assertEq(visibleModeCount(false), 4)
assertEq(visibleModeCount(true), 7)
assertEq(visibleModeIndex(0, false), 1)
assertEq(modeAbbrev(1), "Ion")
var infoAeo6 = cellInfo(0, 4, 5, 1, false, 3)
assertEq(infoAeo6.symbol, "Ab")
assertEq(infoAeo6.numeral, "♭VI")
var dropC = decodeChord(encodeChord(toTriadPayload(ionianI)))
assertEq(dropC.rootPc, 0)
assertEq(dropC.quality, "major")
var dropLoc = decodeChord(encodeChord(toTriadPayload(locTonic)))
assertEq(dropLoc.rootPc, 0)
assertEq(dropLoc.quality, "diminished")
var dropAeolian = decodeChord(encodeChord(toTriadPayload(aeolian6)))
assertEq(dropAeolian.rootPc, 8)
assertEq(dropAeolian.quality, "major")

// Bar-widget status document: the widget must survive a stale, truncated, or
// hostile status.json without ever inventing a playing state.
var statusPlaying = statusDocument(true, "My Song", false)
assertEq(statusPlaying.playing, true)
assertEq(statusPlaying.panelOpen, false)
assertEq(statusPlaying.title, "My Song")
assertEq(statusDocument(1, "x", 1).playing, false, "only true means playing")
assertEq(statusDocument(true, "a\nb\tc", true).title, "a b c", "title is one line")
assertEq(statusDocument(true, null, true).title, "")
var longTitle = ""
while (longTitle.length < 400)
  longTitle += "x"
assertEq(statusDocument(true, longTitle, true).title.length, 120, "title is capped")

assertEq(parseStatus(JSON.stringify(statusPlaying)).playing, true)
assertEq(parseStatus(JSON.stringify(statusPlaying)).title, "My Song")
assertEq(parseStatus("").playing, false)
assertEq(parseStatus("{not json").playing, false)
assertEq(parseStatus("[]").playing, false, "arrays are not a status document")
assertEq(parseStatus("null").playing, false)
assertEq(parseStatus(undefined).playing, false)
assertEq(parseStatus('{"playing":"yes"}').playing, false, "truthy strings are not playing")
assertEq(parseStatus('{"playing":true,"title":"a\\nb"}').title, "a b")

assertEq(tooltipText(false, "My Song", false), "Open Omasong")
assert(tooltipText(true, "My Song", true).indexOf("Playing: My Song") === 0)
assert(tooltipText(true, "My Song", false).indexOf("Playing in background: My Song") === 0)
assert(tooltipText(true, "", true).indexOf("Untitled") >= 0, "blank title falls back")
assertEq(tooltipText(true, "<b>x</b>", true).indexOf("<"), -1, "tooltip markup is neutralized")
