.pragma library

function uid(prefix) {
  return (prefix || "id") + "-" + Date.now().toString(36) + "-" + Math.floor(Math.random() * 1e6).toString(36)
}

function emptySection(name, slots) {
  var count = slots > 0 ? slots : 8
  var chords = []
  for (var i = 0; i < count; i++)
    chords.push("")
  return { id: uid("sec"), name: name || "Verse", chords: chords }
}

function defaultSong() {
  return {
    title: "Untitled",
    tonicIndex: 0,
    bpm: 120,
    loop: true,
    octave: 4,
    layout: "qwerty",
    sections: [
      emptySection("Verse", 8),
      emptySection("Chorus", 8)
    ]
  }
}

function normalizeSong(raw) {
  var song = defaultSong()
  if (!raw || typeof raw !== "object")
    return song
  if (typeof raw.title === "string" && raw.title.trim())
    song.title = raw.title.trim()
  var tonic = Number(raw.tonicIndex)
  if (isFinite(tonic))
    song.tonicIndex = ((tonic % 12) + 12) % 12
  var bpm = Number(raw.bpm)
  if (isFinite(bpm))
    song.bpm = Math.max(40, Math.min(240, Math.round(bpm)))
  song.loop = raw.loop !== false
  var oct = Number(raw.octave)
  if (isFinite(oct))
    song.octave = Math.max(1, Math.min(7, Math.floor(oct)))
  if (raw.layout === "dvorak" || raw.layout === "colemak" || raw.layout === "qwerty")
    song.layout = raw.layout
  if (Array.isArray(raw.sections) && raw.sections.length) {
    song.sections = []
    for (var i = 0; i < raw.sections.length; i++) {
      var src = raw.sections[i] || {}
      var section = emptySection(src.name || ("Section " + (i + 1)), 0)
      section.id = typeof src.id === "string" && src.id ? src.id : section.id
      section.chords = []
      var list = Array.isArray(src.chords) ? src.chords : []
      var count = Math.max(4, list.length || 8)
      for (var c = 0; c < count; c++) {
        var symbol = list[c]
        section.chords.push(typeof symbol === "string" ? symbol : "")
      }
      song.sections.push(section)
    }
  }
  return song
}

function cloneSong(song) {
  return normalizeSong(JSON.parse(JSON.stringify(song || defaultSong())))
}

function mergeSong(song, patch) {
  var next = cloneSong(song)
  if (!patch || typeof patch !== "object")
    return next
  for (var key in patch)
    next[key] = patch[key]
  return normalizeSong(next)
}

function setChord(song, sectionIndex, slot, symbol) {
  var next = cloneSong(song)
  if (!next.sections[sectionIndex])
    return next
  if (slot < 0)
    return next
  while (next.sections[sectionIndex].chords.length <= slot)
    next.sections[sectionIndex].chords.push("")
  next.sections[sectionIndex].chords[slot] = symbol || ""
  return next
}

function addSection(song, name) {
  var next = cloneSong(song)
  next.sections.push(emptySection(name || "Verse", 8))
  return next
}

function removeSection(song, sectionIndex) {
  var next = cloneSong(song)
  if (next.sections.length <= 1)
    return next
  next.sections.splice(sectionIndex, 1)
  return next
}

function renameSection(song, sectionIndex, name) {
  var next = cloneSong(song)
  if (!next.sections[sectionIndex])
    return next
  next.sections[sectionIndex].name = name || next.sections[sectionIndex].name
  return next
}

function flattenSlots(song) {
  var slots = []
  var sections = (song && song.sections) ? song.sections : []
  for (var s = 0; s < sections.length; s++) {
    var chords = sections[s].chords || []
    for (var c = 0; c < chords.length; c++) {
      slots.push({
        sectionIndex: s,
        slot: c,
        symbol: chords[c] || "",
        sectionName: sections[s].name || ""
      })
    }
  }
  return slots
}

function nextFilledSlot(slots, fromIndex) {
  if (!slots || !slots.length)
    return -1
  var start = fromIndex < 0 ? 0 : fromIndex
  for (var i = start; i < slots.length; i++) {
    if (slots[i].symbol && String(slots[i].symbol).trim())
      return i
  }
  return -1
}

function slotCount(song) {
  return flattenSlots(song).length
}

function transposeSong(song, semitones, transposeFn) {
  var next = cloneSong(song)
  if (!semitones)
    return next
  for (var s = 0; s < next.sections.length; s++) {
    var chords = next.sections[s].chords
    for (var c = 0; c < chords.length; c++) {
      if (chords[c])
        chords[c] = transposeFn(chords[c], semitones)
    }
  }
  return next
}
