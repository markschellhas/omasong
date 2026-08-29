import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import qs.Commons
import qs.Ui
import "js/Model.js" as Model
import "js/Song.js" as Song
import "js/Keyboard.js" as KeyMap

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
  readonly property var timeline: Song.buildTimeline(song)

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
    return next
  }

  function open(payloadJson) {
    opened = true
    Qt.callLater(function() { keyCatcher.forceActiveFocus() })
  }

  function close() {
    stopPlayback()
    opened = false
  }

  function dismiss() {
    close()
    if (shell && typeof shell.hide === "function")
      shell.hide((manifest && manifest.id) || "io.github.markschellhas.songwriter")
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
    var loop = next && next.loop !== undefined ? next.loop : (song && song.loop)
    var octave = next && next.octave !== undefined ? next.octave : (song && song.octave)
    var layout = next && next.layout !== undefined ? next.layout : (song && song.layout)
    var normalized = Song.normalizeSong(next)
    if (loop !== undefined)
      normalized.loop = loop
    if (octave !== undefined)
      normalized.octave = octave
    if (layout !== undefined)
      normalized.layout = layout
    song = normalized
    clampSelection()
    persistSoon()
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
  }

  function playFreqs(freqs, seconds) {
    if (!freqs || !freqs.length)
      return
    var cmd = ["python3", playScript]
    for (var i = 0; i < freqs.length; i++)
      cmd.push(String(freqs[i]))
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
    if (fields.keyIndex !== undefined)
      next.keyIndex = fields.keyIndex
    updateSong(next)
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
    for (i = 0; i < soundingNotes.length; i++)
      add(soundingNotes[i])
    for (i = 0; i < previewNotes.length; i++)
      add(previewNotes[i])
    for (var held in heldNotes)
      add(held)
    activeNotes = next
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

  function applySounding(event) {
    if (!event || event.rest || !event.chord) {
      soundingNotes = []
      refreshPiano()
      return
    }
    soundingNotes = Model.triadMidi(event.chord, song.octave)
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
      if (event.rest || !event.chord)
        statusText = name ? name + " · Rest" : "Rest"
      else
        statusText = name + " · " + Model.chordName(event.chord.rootPc, event.chord.quality)
      applySounding(event)
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
    refreshPiano()
  }

  function auditionSlot(sectionIndex, measureIndex, slotIndex) {
    stopPlayback()
    var chord = Song.getChord(song, sectionIndex, measureIndex, slotIndex)
    if (!chord)
      return
    var section = song.sections[sectionIndex]
    var slot = section.measures[measureIndex].slots[slotIndex]
    var beats = Song.slotDurationBeats(slot.span, section.timeSig && section.timeSig.denominator)
    var seconds = Song.beatsToSeconds(beats, song.bpm)
    statusText = Model.chordName(chord.rootPc, chord.quality)
    playMidiNotes(Model.triadMidi(chord, song.octave), seconds)
  }

  function handleComputerKey(event) {
    var midi = KeyMap.midiForKey(event.text, song.octave, song.layout)
    if (midi < 0)
      return
    if (heldNotes[midi] || heldNotes[String(midi)])
      return
    var nextHeld = {}
    for (var held in heldNotes)
      nextHeld[held] = heldNotes[held]
    nextHeld[midi] = true
    heldNotes = nextHeld
    var next = activeNotes.slice()
    if (next.indexOf(midi) === -1)
      next.push(midi)
    activeNotes = next
    playMidiNotes([midi], 0.45)
    event.accepted = true
  }

  function handleComputerKeyUp(event) {
    if (event.key === Qt.Key_Space) {
      event.accepted = true
      return
    }
    var midi = KeyMap.midiForKey(event.text, song.octave, song.layout)
    if (midi < 0)
      return
    var nextHeld = {}
    for (var held in heldNotes) {
      if (String(held) !== String(midi))
        nextHeld[held] = heldNotes[held]
    }
    heldNotes = nextHeld
    refreshPiano()
    event.accepted = true
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
        if (raw && String(raw).trim())
          song = seedSong(JSON.parse(raw))
      } catch (e) {
        song = seedSong(Song.defaultSong())
      }
      persistReady = true
      persistFallback.stop()
    }
    onLoadFailed: {
      persistReady = true
      persistFallback.stop()
    }
  }

  Timer {
    id: persistFallback
    interval: 2000
    running: true
    onTriggered: {
      if (!persistReady)
        persistReady = true
    }
  }

  Component.onCompleted: songFile.reload()

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
            circle.step(-1)
            event.accepted = true
            return
          }
          if (event.key === Qt.Key_Right) {
            circle.step(1)
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
          root.handleComputerKey(event)
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
          return Math.min(Style.space(340), Math.max(Style.space(230), Math.floor(rest / 3)))
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
            text: "Circle of fifths, song structure, and keyboard"
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

        CircleOfFifths {
          id: circle
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: transport.bottom
          height: content.circleHeight
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
            if (!triad)
              return
            root.statusText = triad.label
            root.playMidiNotes(triad.notes, 0.7)
          }
        }

        SongStructure {
          id: structure
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.top: circle.bottom
          anchors.bottom: piano.top
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
          chordDragPayload: circle.chordDragPayload
          onChordDropped: function(sectionIndex, measureIndex, slotIndex, chord, insertAfter) {
            root.updateSong(Song.placeChord(root.song, sectionIndex, measureIndex, slotIndex, chord, insertAfter))
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
            root.selectedSection = sectionIndex
            root.selectedMeasure = measureIndex
            root.selectedSlot = slotIndex
          }
        }

        Piano {
          id: piano
          anchors.left: parent.left
          anchors.right: parent.right
          anchors.bottom: parent.bottom
          height: root.pianoHeight
          foreground: root.foreground
          dim: root.dim
          octave: root.song.octave
          layoutName: root.song.layout
          activeNotes: root.activeNotes
          onNoteOn: function(midi) { root.playMidiNotes([midi], 0.45) }
          onNoteOff: function(midi) {
            root.previewNotes = root.previewNotes.filter(function(n) { return n !== midi })
            root.refreshPiano()
          }
          onOctaveChangedByUser: function(value) {
            root.applySongFields({ octave: KeyMap.clampOctave(value) })
            root.refocusKeys()
          }
        }
      }
      }
    }
  }
}
