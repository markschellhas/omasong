import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui
import "js/Model.js" as Model
import "js/Song.js" as Song
import "js/Agent.js" as Agent
import "js/Keyboard.js" as KeyMap
import "js/Focus.js" as Focus

Item {
  id: root

  property string omarchyPath: Quickshell.env("OMARCHY_PATH")
  property var shell: null
  property var manifest: null
  property bool opened: false

  property color background: Color.menu.background
  property color foreground: Color.menu.text
  property color border: Color.menu.border
  property color dim: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.56)
  property color faint: Qt.rgba(foreground.r, foreground.g, foreground.b, 0.12)

  property var song: seedSong(Song.defaultSong())
  property bool playing: false
  property var playEvent: null
  property int fillSection: -1
  property int fillMeasure: -1
  property int fillSlot: -1
  property real fillTotalBeats: 0
  property real fillBaseProgress: 0
  property real fillSegmentStartedMs: 0
  property bool fillAudition: false
  property real slotFillProgress: 0
  property int currentBar: 1
  property real currentBeat: 0
  property int displayBeat: 1
  property int selectedSection: 0
  property int selectedMeasure: 0
  property int selectedSlot: 0
  property var activeNotes: []
  property var soundingNotes: []
  property var previewNotes: []
  property var heldNotes: ({})
  property string statusText: ""
  property bool persistReady: false
  property int navRegion: 0
  readonly property var timeline: Song.buildTimeline(song)
  readonly property bool laptopKeys: !!(song && song.laptopKeys)
  readonly property int laptopOctave: KeyMap.clampOctave(song && song.laptopOctave)
  readonly property string headerHint: {
    var name = Focus.regionName(navRegion)
    if (root.laptopKeys)
      return name + " · Laptop keys on"
    return name
  }

  readonly property int cardWidth: Math.min(Style.space(1180), panel.width - Style.gapsOut * 2)
  readonly property int cardHeight: Math.min(Style.space(820), panel.height - Style.gapsOut * 2)
  readonly property int headerHeight: Style.space(52)
  readonly property int transportHeight: Style.space(44)
  readonly property int pianoHeight: Style.space(146)
  readonly property string playScript: decodeURIComponent(
    Qt.resolvedUrl("play-notes.py").toString().replace(/^file:\/\//, ""))
  readonly property string songPath: Quickshell.env("HOME") + "/.local/state/omarchy/songwriter/song.json"
  readonly property string writeScript: decodeURIComponent(
    Qt.resolvedUrl("write-json.py").toString().replace(/^file:\/\//, ""))
  readonly property string agentServerScript: decodeURIComponent(
    Qt.resolvedUrl("agent-server.py").toString().replace(/^file:\/\//, ""))
  readonly property string agentHome: {
    var override = Quickshell.env("CHORDS_AGENT_HOME")
    if (override && String(override).length)
      return override
    return Quickshell.env("HOME") + "/.config/chords-and-tabs"
  }
  readonly property int agentPort: {
    var env = Quickshell.env("CHORDS_AGENT_PORT")
    var n = Number(env)
    if (env && env.length && isFinite(n) && n >= 0 && n <= 65535)
      return Math.round(n)
    return 17891
  }
  readonly property string agentSongPath: agentHome + "/song.json"
  readonly property string agentProgressionsPath: agentHome + "/progressions.json"
  readonly property string agentApiPath: agentHome + "/agent-api.json"
  function seedSong(raw) {
    var next = Song.normalizeSong(raw)
    if (raw && raw.loop !== undefined)
      next.loop = !!raw.loop
    else
      next.loop = true
    if (raw && raw.octave !== undefined)
      next.octave = raw.octave
    if (raw && raw.layout !== undefined)
      next.layout = raw.layout
    if (raw && raw.instrument !== undefined)
      next.instrument = KeyMap.clampInstrument(raw.instrument)
    else
      next.instrument = 0
    next.laptopKeys = !!(raw && raw.laptopKeys)
    next.laptopOctave = raw && raw.laptopOctave !== undefined
      ? KeyMap.clampOctave(raw.laptopOctave)
      : KeyMap.DEFAULT_OCTAVE
    return next
  }

  function open(payloadJson) {
    opened = true
    startAgentServer()
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function close() {
    stopPlayback()
    opened = false
    stopAgentServer()
  }

  function dismiss() {
    close()
    if (shell && typeof shell.hide === "function")
      shell.hide((manifest && manifest.id) || "markschellhas.songwriter")
  }

  function startAgentServer() {
    agentServer.running = true
  }

  function stopAgentServer() {
    agentServer.running = false
  }

  function clampSelection() {
    var sections = (song && song.sections) ? song.sections : []
    if (!sections.length) {
      selectedSection = 0
      selectedMeasure = 0
      selectedSlot = 0
      return
    }
    if (selectedSection >= sections.length)
      selectedSection = sections.length - 1
    if (selectedSection < 0)
      selectedSection = 0
    var measures = sections[selectedSection].measures || []
    if (selectedMeasure >= measures.length)
      selectedMeasure = Math.max(0, measures.length - 1)
    if (selectedMeasure < 0)
      selectedMeasure = 0
    var slots = (measures[selectedMeasure] && measures[selectedMeasure].slots) || []
    if (selectedSlot >= slots.length)
      selectedSlot = Math.max(0, slots.length - 1)
    if (selectedSlot < 0)
      selectedSlot = 0
  }

  function textFieldHasFocus() {
    var item = keyCatcher.activeFocusItem
    if (!item)
      return structure.renaming
    return (item instanceof TextInput) || structure.renaming
  }

  function refocusKeys() {
    if (textFieldHasFocus())
      return
    keyCatcher.forceActiveFocus()
  }

  function updateSong(next) {
    var prevBpm = song && song.bpm
    var loop = next && next.loop !== undefined ? next.loop : (song && song.loop)
    var octave = next && next.octave !== undefined ? next.octave : (song && song.octave)
    var layout = next && next.layout !== undefined ? next.layout : (song && song.layout)
    var instrument = next && next.instrument !== undefined ? next.instrument : (song && song.instrument)
    var laptopKeys = next && next.laptopKeys !== undefined ? next.laptopKeys : (song && song.laptopKeys)
    var laptopOctave = next && next.laptopOctave !== undefined ? next.laptopOctave : (song && song.laptopOctave)
    var normalized = Song.normalizeSong(next)
    if (loop !== undefined)
      normalized.loop = loop
    if (octave !== undefined)
      normalized.octave = octave
    if (layout !== undefined)
      normalized.layout = layout
    if (instrument !== undefined)
      normalized.instrument = KeyMap.clampInstrument(instrument)
    normalized.laptopKeys = !!laptopKeys
    normalized.laptopOctave = KeyMap.clampOctave(laptopOctave)
    song = normalized
    if (fillSection >= 0 && prevBpm !== undefined && normalized.bpm !== prevBpm)
      retimeFillForBpm()
    clampSelection()
    persistSoon()
    refreshPiano()
  }

  function persistSoon() {
    if (!persistReady)
      return
    persistTimer.restart()
  }

  function persistNow() {
    if (!persistReady)
      return
    Quickshell.execDetached(["python3", writeScript, songPath, JSON.stringify(song)])
    Quickshell.execDetached(["python3", writeScript, agentSongPath, JSON.stringify(Agent.songJson(song))])
    Quickshell.execDetached(["python3", writeScript, agentProgressionsPath, JSON.stringify(Agent.progressionsJson(song))])
    Quickshell.execDetached(["python3", writeScript, agentApiPath, JSON.stringify({ port: agentPort })])
  }

  function currentInstrument() {
    return KeyMap.clampInstrument(song && song.instrument)
  }

  function playFreqs(freqs, seconds) {
    if (!freqs || !freqs.length)
      return
    var cmd = ["python3", playScript]
    for (var i = 0; i < freqs.length; i++)
      cmd.push(String(freqs[i]))
    cmd.push("--instrument", String(currentInstrument()))
    if (seconds)
      cmd.push("--seconds", String(seconds))
    Quickshell.execDetached(cmd)
  }

  function playMidiNotes(notes, seconds) {
    if (!notes || !notes.length)
      return
    var cmd = ["python3", playScript, "--midi"]
    for (var i = 0; i < notes.length; i++)
      cmd.push(String(notes[i]))
    cmd.push("--instrument", String(currentInstrument()))
    if (seconds)
      cmd.push("--seconds", String(seconds))
    Quickshell.execDetached(cmd)
    previewNotes = notes.slice()
    refreshPiano()
    noteClear.interval = Math.max(80, Math.round((seconds || 0.7) * 1000))
    noteClear.restart()
  }

  function applySongFields(fields) {
    var next = Song.cloneSong(song)
    if (fields.bpm !== undefined)
      next = Song.setBpm(next, fields.bpm)
    next.loop = fields.loop !== undefined ? !!fields.loop : !!(song && song.loop)
    next.octave = fields.octave !== undefined ? fields.octave : (song && song.octave)
    next.layout = fields.layout !== undefined ? fields.layout : (song && song.layout)
    next.instrument = fields.instrument !== undefined ? fields.instrument : (song && song.instrument)
    next.laptopKeys = fields.laptopKeys !== undefined ? !!fields.laptopKeys : !!(song && song.laptopKeys)
    next.laptopOctave = fields.laptopOctave !== undefined ? fields.laptopOctave : (song && song.laptopOctave)
    if (fields.keyIndex !== undefined)
      next.keyIndex = fields.keyIndex
    updateSong(next)
  }

  function selectedSlotNotes() {
    var chord = Song.getChord(song, selectedSection, selectedMeasure, selectedSlot)
    if (!chord)
      return []
    return Model.triadMidi(chord)
  }

  function refreshPiano() {
    var next = []
    function add(n) {
      var midi = Number(n)
      if (!isFinite(midi))
        return
      midi = Math.round(midi)
      if (next.indexOf(midi) === -1)
        next.push(midi)
    }
    var i
    var selected = selectedSlotNotes()
    for (i = 0; i < soundingNotes.length; i++)
      add(soundingNotes[i])
    for (i = 0; i < previewNotes.length; i++)
      add(previewNotes[i])
    for (i = 0; i < selected.length; i++)
      add(selected[i])
    for (var held in heldNotes)
      add(held)
    activeNotes = next
  }

  function holdLiveNote(midi) {
    if (heldNotes[midi] || heldNotes[String(midi)])
      return
    var nextHeld = {}
    for (var held in heldNotes)
      nextHeld[held] = heldNotes[held]
    nextHeld[midi] = true
    heldNotes = nextHeld
    playMidiNotes([midi], 0.45)
  }

  function releaseLiveNote(midi) {
    var nextHeld = {}
    for (var held in heldNotes) {
      if (String(held) !== String(midi))
        nextHeld[held] = heldNotes[held]
    }
    heldNotes = nextHeld
    previewNotes = previewNotes.filter(function(n) { return n !== midi })
    refreshPiano()
  }

  function measureStartBeat(events, event) {
    if (!events || !event)
      return 0
    for (var i = 0; i < events.length; i++) {
      var e = events[i]
      if (e.sectionIndex === event.sectionIndex
          && e.measureIndex === event.measureIndex
          && e.repeatPass === event.repeatPass)
        return e.startBeat
    }
    return event.startBeat
  }

  function sameEventIdentity(a, b) {
    return !!(a && b
      && a.sectionIndex === b.sectionIndex
      && a.measureIndex === b.measureIndex
      && a.slotIndex === b.slotIndex
      && a.repeatPass === b.repeatPass)
  }

  function clearSlotFill() {
    fillSection = -1
    fillMeasure = -1
    fillSlot = -1
    fillTotalBeats = 0
    fillBaseProgress = 0
    fillSegmentStartedMs = 0
    fillAudition = false
    slotFillProgress = 0
    fillClock.stop()
  }

  function updateFillProgress() {
    if (fillSection < 0 || !(fillTotalBeats > 0)) {
      slotFillProgress = 0
      return
    }
    var segmentBeats = (Date.now() - fillSegmentStartedMs) / 1000 * song.bpm / 60
    slotFillProgress = Math.min(1, fillBaseProgress + segmentBeats / fillTotalBeats)
    if (slotFillProgress >= 1 && fillAudition)
      clearSlotFill()
  }

  function beginSlotFill(sectionIndex, measureIndex, slotIndex, beats, audition) {
    fillSection = sectionIndex
    fillMeasure = measureIndex
    fillSlot = slotIndex
    fillAudition = !!audition
    fillTotalBeats = beats
    fillBaseProgress = 0
    fillSegmentStartedMs = Date.now()
    slotFillProgress = 0
    fillClock.start()
  }

  function retimeFillForBpm() {
    if (fillSection < 0 || !(fillTotalBeats > 0))
      return
    updateFillProgress()
    fillBaseProgress = slotFillProgress
    fillSegmentStartedMs = Date.now()
  }

  function applySounding(event) {
    if (!event || event.rest || !event.chord) {
      soundingNotes = []
      refreshPiano()
      return
    }
    soundingNotes = Model.triadMidi(event.chord)
    playMidiNotes(soundingNotes, Song.beatsToSeconds(event.durationBeats, song.bpm))
  }

  function applyPlayhead(event) {
    if (!event) {
      stopPlayback()
      return
    }
    if (playEvent
        && currentBeat !== 0
        && (playEvent.sectionIndex !== event.sectionIndex
          || playEvent.measureIndex !== event.measureIndex
          || playEvent.repeatPass !== event.repeatPass))
      currentBar += 1
    if (currentBeat === 0)
      currentBar = 1
    var changed = !sameEventIdentity(playEvent, event)
    playEvent = event
    if (changed) {
      var name = (song.sections[event.sectionIndex] || {}).name || ""
      if (event.rest || !event.chord) {
        statusText = name ? name + " · Rest" : "Rest"
        clearSlotFill()
      } else {
        statusText = name + " · " + Model.chordName(event.chord.rootPc, event.chord.quality)
        beginSlotFill(event.sectionIndex, event.measureIndex, event.slotIndex, event.durationBeats, false)
      }
      applySounding(event)
    } else if (playing && !event.rest && event.chord) {
      updateFillProgress()
    }
    displayBeat = Math.max(1, Math.floor(currentBeat - measureStartBeat(timeline, event)) + 1)
  }

  function scheduleBeatTick() {
    var delta = Song.beatTickDelta(timeline, currentBeat)
    if (!(delta > 0)) {
      stopPlayback()
      return
    }
    transportTimer.interval = Math.max(1, Math.round(Song.beatsToSeconds(delta, song.bpm) * 1000))
    transportTimer.restart()
  }

  function startPlayback() {
    var tl = timeline
    if (!tl || !tl.length) {
      statusText = "Add chords to play"
      return
    }
    playing = true
    currentBeat = 0
    currentBar = 1
    playEvent = null
    applyPlayhead(Song.eventAtBeat(tl, currentBeat))
    scheduleBeatTick()
  }

  function stopPlayback() {
    playing = false
    playEvent = null
    currentBeat = 0
    currentBar = 1
    displayBeat = 1
    soundingNotes = []
    transportTimer.stop()
    clearSlotFill()
    refreshPiano()
  }

  function auditionSlot(sectionIndex, measureIndex, slotIndex) {
    stopPlayback()
    var chord = Song.getChord(song, sectionIndex, measureIndex, slotIndex)
    if (!chord)
      return
    var beats = Song.slotDurationBeatsAt(song, sectionIndex, measureIndex, slotIndex)
    if (!(beats > 0))
      return
    var seconds = Song.beatsToSeconds(beats, song.bpm)
    statusText = Model.chordName(chord.rootPc, chord.quality)
    beginSlotFill(sectionIndex, measureIndex, slotIndex, beats, true)
    playMidiNotes(Model.triadMidi(chord), seconds)
  }

  function laptopKeyText(event) {
    if (event.key === Qt.Key_Z)
      return "z"
    if (event.key === Qt.Key_X)
      return "x"
    if (!event.text)
      return ""
    return String(event.text).toLowerCase()
  }

  function handleComputerKey(event) {
    if (!root.laptopKeys)
      return
    var key = laptopKeyText(event)
    if (key === "z") {
      if (!event.isAutoRepeat)
        applySongFields({ laptopOctave: KeyMap.shiftOctave(root.laptopOctave, -1) })
      event.accepted = true
      return
    }
    if (key === "x") {
      if (!event.isAutoRepeat)
        applySongFields({ laptopOctave: KeyMap.shiftOctave(root.laptopOctave, 1) })
      event.accepted = true
      return
    }
    var midi = KeyMap.midiForLaptopKey(key, root.laptopOctave)
    if (midi < 0)
      return
    holdLiveNote(midi)
    event.accepted = true
  }

  function handleComputerKeyUp(event) {
    if (event.key === Qt.Key_Space) {
      event.accepted = true
      return
    }
    if (!root.laptopKeys)
      return
    var midi = KeyMap.midiForLaptopKey(laptopKeyText(event), root.laptopOctave)
    if (midi < 0)
      return
    releaseLiveNote(midi)
    event.accepted = true
  }

  function focusRegion(index) {
    navRegion = index
  }

  function moveNavRegion(delta) {
    navRegion = Focus.cycleNavRegion(navRegion, delta)
  }

  function applyHorizontalNav(delta) {
    if (navRegion === 0) {
      circle.step(delta)
      return
    }
    if (navRegion === 2)
      applySongFields({ instrument: KeyMap.wrapInstrument(currentInstrument() + delta) })
  }

  function moveSelectedCell(delta) {
    if (navRegion !== 1)
      return false
    var sections = song && song.sections ? song.sections : []
    var cells = []
    var currentIndex = -1
    var i
    var j
    var k
    for (i = 0; i < sections.length; i++) {
      var measures = sections[i] && sections[i].measures ? sections[i].measures : []
      for (j = 0; j < measures.length; j++) {
        var slots = measures[j] && measures[j].slots ? measures[j].slots : []
        for (k = 0; k < slots.length; k++) {
          cells.push({ section: i, measure: j, slot: k })
          if (i === selectedSection && j === selectedMeasure && k === selectedSlot)
            currentIndex = cells.length - 1
        }
      }
    }
    if (!cells.length)
      return false
    var direction = Number(delta) < 0 ? -1 : 1
    if (currentIndex < 0)
      currentIndex = direction > 0 ? -1 : cells.length
    var nextIndex = (currentIndex + direction) % cells.length
    if (nextIndex < 0)
      nextIndex += cells.length
    var next = cells[nextIndex]
    selectedSection = next.section
    selectedMeasure = next.measure
    selectedSlot = next.slot
    refreshPiano()
    return true
  }

  function clearSelectedSlot() {
    if (textFieldHasFocus())
      return false
    if (navRegion !== 1)
      return false
    if (!Song.getChord(song, selectedSection, selectedMeasure, selectedSlot))
      return false
    updateSong(Song.setChord(song, selectedSection, selectedMeasure, selectedSlot, null))
    return true
  }

  function previewCircleDegree(event) {
    if (navRegion !== 0 || root.laptopKeys)
      return false
    var degree = Focus.degreeIndexFromKey(event.key, event.text)
    if (degree < 0)
      return false
    focusRegion(0)
    circle.previewChip(degree)
    return true
  }

  function handleNavKey(event) {
    if (root.laptopKeys)
      return
    var down = event.key === Qt.Key_J || event.text === "j" || event.text === "J"
    var up = event.key === Qt.Key_K || event.text === "k" || event.text === "K"
    var left = event.key === Qt.Key_H || event.text === "h" || event.text === "H"
    var right = event.key === Qt.Key_L || event.text === "l" || event.text === "L"
    if (down) {
      moveNavRegion(1)
      event.accepted = true
      return
    }
    if (up) {
      moveNavRegion(-1)
      event.accepted = true
      return
    }
    if (left) {
      applyHorizontalNav(-1)
      event.accepted = true
      return
    }
    if (right) {
      applyHorizontalNav(1)
      event.accepted = true
    }
  }

  Timer {
    id: persistTimer
    interval: 250
    onTriggered: persistNow()
  }

  Timer {
    id: noteClear
    interval: 700
    onTriggered: {
      root.previewNotes = []
      root.refreshPiano()
    }
  }

  Timer {
    id: fillClock
    interval: 16
    repeat: true
    running: false
    onTriggered: root.updateFillProgress()
  }

  Timer {
    id: transportTimer
    interval: 1000
    repeat: false
    onTriggered: {
      var delta = Song.beatTickDelta(timeline, currentBeat)
      currentBeat += delta
      var total = Song.timelineDurationBeats(timeline)
      if (currentBeat >= total) {
        if (song.loop) {
          currentBeat = 0
          currentBar = 1
          playEvent = null
        } else {
          stopPlayback()
          return
        }
      }
      applyPlayhead(Song.eventAtBeat(timeline, currentBeat))
      scheduleBeatTick()
    }
  }

  FileView {
    id: songFile
    path: root.songPath
    preload: true
    blockLoading: false
    printErrors: false
    onLoaded: {
      try {
        var raw = text()
        if (raw && String(raw).trim()) {
          var parsed = JSON.parse(raw)
          if (Song.looksLikeSongDocument(parsed))
            song = seedSong(parsed)
          else
            song = seedSong(Song.defaultSong())
        }
      } catch (e) {
        song = seedSong(Song.defaultSong())
      }
      persistReady = true
      persistFallback.stop()
      persistNow()
      refreshPiano()
    }
    onLoadFailed: {
      persistReady = true
      persistFallback.stop()
      persistNow()
    }
  }

  Timer {
    id: persistFallback
    interval: 2000
    running: true
    onTriggered: {
      if (!persistReady) {
        persistReady = true
        persistNow()
      }
    }
  }

  Process {
    id: agentServer
    running: false
    command: ["python3", root.agentServerScript, "--home", root.agentHome, "--port", String(root.agentPort)]
  }

  Component.onCompleted: {
    songFile.reload()
    refreshPiano()
  }

  Component.onDestruction: stopAgentServer()

  PanelWindow {
    id: panel
    visible: root.opened
    anchors { top: true; bottom: true; left: true; right: true }
    mask: Region { item: card }
    color: "transparent"
    WlrLayershell.namespace: "omarchy-songwriter"
    WlrLayershell.layer: WlrLayer.Overlay
    WlrLayershell.keyboardFocus: root.opened && cardHover.hovered
      ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None
    exclusionMode: ExclusionMode.Ignore

    BorderSurface {
      id: card
      width: root.cardWidth
      height: root.cardHeight
      anchors.centerIn: parent
      color: root.background
      borderSpec: Border.surfaceSpec("menu", "border", root.border, Math.max(1, Style.normalBorderWidth))
      radius: Style.cornerRadius

      HoverHandler {
        id: cardHover
        onHoveredChanged: if (hovered) root.refocusKeys()
      }

      FocusScope {
        id: keyCatcher
        anchors.fill: parent
        focus: true

        Keys.priority: Keys.AfterItem
        Keys.onPressed: function(event) {
          if (event.key === Qt.Key_Escape) {
            if (structure.renaming) {
              structure.cancelRename()
              event.accepted = true
              return
            }
            root.dismiss()
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Left) {
            root.applyHorizontalNav(-1)
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Right) {
            root.applyHorizontalNav(1)
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Up) {
            root.moveNavRegion(-1)
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Down) {
            root.moveNavRegion(1)
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Tab || event.key === Qt.Key_Backtab) {
            if (root.textFieldHasFocus())
              return
            var direction = (event.key === Qt.Key_Backtab
              || (event.modifiers & Qt.ShiftModifier)) ? -1 : 1
            if (root.moveSelectedCell(direction))
              event.accepted = true
            return
          }
          if (event.key === Qt.Key_Space) {
            if (event.isAutoRepeat) {
              event.accepted = true
              return
            }
            if (root.playing)
              root.stopPlayback()
            else
              root.startPlayback()
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Delete || event.key === Qt.Key_Backspace) {
            if (root.clearSelectedSlot())
              event.accepted = true
            return
          }
          if (root.previewCircleDegree(event))
            return
          if (root.laptopKeys)
            root.handleComputerKey(event)
          else
            root.handleNavKey(event)
        }
        Keys.onReleased: function(event) {
          root.handleComputerKeyUp(event)
        }

        Item {
          id: content
          anchors.fill: parent
          anchors.margins: Style.spacing.md

        readonly property int circleHeight: {
          var rest = height - root.headerHeight - root.transportHeight - root.pianoHeight
          return Math.min(Style.space(560), Math.max(Style.space(468), Math.floor(rest / 3) + Style.space(180)))
        }

        Item {
          id: header
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: parent.top
          height: root.headerHeight

          Text {
            id: title
            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: closeButton.left
            anchors.rightMargin: Style.spacing.sm
            height: Style.space(30)
            text: "Chords & Tabs"
            color: root.foreground
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.heading
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
          }

          Text {
            anchors.top: title.bottom
            anchors.left: parent.left
            anchors.right: closeButton.left
            anchors.rightMargin: Style.spacing.sm
            anchors.bottom: parent.bottom
            text: root.headerHint
            textFormat: Text.PlainText
            color: root.dim
            font.family: Style.font.menuFamily
            font.pixelSize: Style.font.caption
            horizontalAlignment: Text.AlignHCenter
            verticalAlignment: Text.AlignVCenter
            elide: Text.ElideRight
          }

          Button {
            id: closeButton
            anchors.right: parent.right
            anchors.verticalCenter: parent.verticalCenter
            iconText: "\uf00d"
            tooltipText: "Close"
            focusable: true
            foreground: root.foreground
            accent: Color.accent
            onClicked: root.dismiss()
          }
        }

        Transport {
          id: transport
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: header.bottom
          height: root.transportHeight
          foreground: root.foreground
          dim: root.dim
          bpm: root.song.bpm
          playing: root.playing
          looping: root.song.loop
          currentBar: root.currentBar
          currentBeat: root.displayBeat
          statusText: root.statusText
          onPlayRequested: { root.startPlayback(); root.refocusKeys() }
          onStopRequested: { root.stopPlayback(); root.refocusKeys() }
          onLoopToggled: {
            root.applySongFields({ loop: !root.song.loop })
            root.refocusKeys()
          }
          onBpmChangedByUser: function(value) {
            root.applySongFields({ bpm: value })
          }
        }

        Item {
          id: circleHost
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: transport.bottom
          height: content.circleHeight

          MouseArea {
            anchors.fill: parent
            onPressed: root.focusRegion(0)
          }

          Rectangle {
            anchors.fill: parent
            visible: root.navRegion === 0
            color: "transparent"
            border.width: Math.max(1, Style.normalBorderWidth)
            border.color: root.foreground
            radius: Math.max(2, Style.cornerRadius / 2)
          }

          CircleOfFifths {
            id: circle
            anchors.fill: parent
            anchors.margins: Style.space(2)
            foreground: root.foreground
            dim: root.dim
            faint: root.faint
            keyIndex: root.song.keyIndex
            onTonicPicked: function(index, ring) {
              if (index === root.song.keyIndex)
                return
              var next = Song.cloneSong(root.song)
              next.keyIndex = index
              root.updateSong(Song.normalizeSong(next))
            }
            onChordPreviewed: function(index, ring, triad) {
              root.focusRegion(0)
              if (!triad)
                return
              root.statusText = triad.label
              root.playMidiNotes(triad.notes, 0.7)
            }
          }
        }

        Item {
          id: structureHost
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: circleHost.bottom
          anchors.bottom: pianoHost.top

          MouseArea {
            anchors.fill: parent
            onPressed: root.focusRegion(1)
          }

          Rectangle {
            anchors.fill: parent
            visible: root.navRegion === 1
            color: "transparent"
            border.width: Math.max(1, Style.normalBorderWidth)
            border.color: root.foreground
            radius: Math.max(2, Style.cornerRadius / 2)
          }

          SongStructure {
            id: structure
            anchors.fill: parent
            anchors.margins: Style.space(2)
            foreground: root.foreground
            dim: root.dim
            faint: root.faint
            sections: root.song.sections
            selectedSection: root.selectedSection
            selectedMeasure: root.selectedMeasure
            selectedSlot: root.selectedSlot
            playSection: root.playing && root.playEvent ? root.playEvent.sectionIndex : -1
            playMeasure: root.playing && root.playEvent ? root.playEvent.measureIndex : -1
            playSlot: root.playing && root.playEvent ? root.playEvent.slotIndex : -1
            fillSection: root.fillSection
            fillMeasure: root.fillMeasure
            fillSlot: root.fillSlot
            slotFillProgress: root.slotFillProgress
            chordDragPayload: circle.chordDragPayload
            onChordDropped: function(sectionIndex, measureIndex, slotIndex, chord, insertAfter) {
              root.updateSong(Song.placeChord(root.song, sectionIndex, measureIndex, slotIndex, chord, insertAfter))
            }
            onChordMoved: function(fromSection, fromMeasure, fromSlot, toSection, toMeasure, toSlot, insertAfter) {
              root.updateSong(Song.moveChord(
                root.song,
                fromSection,
                fromMeasure,
                fromSlot,
                toSection,
                toMeasure,
                toSlot,
                insertAfter
              ))
            }
            onSlotResized: function(sectionIndex, measureIndex, slotIndex, newSpan, edge) {
              root.updateSong(Song.resizeSlot(root.song, sectionIndex, measureIndex, slotIndex, newSpan, edge))
            }
            onSlotCleared: function(sectionIndex, measureIndex, slotIndex) {
              root.updateSong(Song.setChord(root.song, sectionIndex, measureIndex, slotIndex, null))
            }
            onSlotAuditioned: function(sectionIndex, measureIndex, slotIndex) {
              root.auditionSlot(sectionIndex, measureIndex, slotIndex)
            }
            onSectionAdded: function(name) {
              root.updateSong(Song.addSection(root.song, name))
            }
            onSectionRemoved: function(sectionIndex) {
              root.updateSong(Song.removeSection(root.song, sectionIndex))
            }
            onSectionRenamed: function(sectionIndex, name) {
              root.updateSong(Song.renameSection(root.song, sectionIndex, name))
            }
            onTimeSignatureChanged: function(sectionIndex, numerator, denominator) {
              root.updateSong(Song.setTimeSignature(root.song, sectionIndex, {
                numerator: numerator,
                denominator: denominator
              }))
            }
            onRowRepeatToggled: function(sectionIndex, rowIndex, shouldRepeat) {
              root.updateSong(Song.setRowRepeat(root.song, sectionIndex, rowIndex, shouldRepeat))
            }
            onSlotSelected: function(sectionIndex, measureIndex, slotIndex) {
              root.focusRegion(1)
              root.selectedSection = sectionIndex
              root.selectedMeasure = measureIndex
              root.selectedSlot = slotIndex
              root.refreshPiano()
            }
          }
        }

        Item {
          id: pianoHost
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.bottom: parent.bottom
          height: root.pianoHeight

          MouseArea {
            anchors.fill: parent
            onPressed: root.focusRegion(2)
          }

          Rectangle {
            anchors.fill: parent
            visible: root.navRegion === 2
            color: "transparent"
            border.width: Math.max(1, Style.normalBorderWidth)
            border.color: root.foreground
            radius: Math.max(2, Style.cornerRadius / 2)
          }

          Piano {
            id: piano
            anchors.fill: parent
            anchors.margins: Style.space(2)
            foreground: root.foreground
            dim: root.dim
            octave: root.laptopOctave
            instrument: root.song.instrument !== undefined ? root.song.instrument : 0
            layoutName: root.song.layout
            laptopKeys: root.laptopKeys
            activeNotes: root.activeNotes
            onNoteOn: function(midi) {
              root.focusRegion(2)
              root.holdLiveNote(midi)
            }
            onNoteOff: function(midi) { root.releaseLiveNote(midi) }
            onInstrumentChangedByUser: function(value) {
              root.focusRegion(2)
              root.applySongFields({ instrument: KeyMap.wrapInstrument(value) })
              root.refocusKeys()
            }
            onLaptopToggled: {
              root.focusRegion(2)
              root.applySongFields({ laptopKeys: !root.laptopKeys })
              root.refocusKeys()
            }
          }
        }
      }
      }
    }
  }
}
